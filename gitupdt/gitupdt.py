import os
import sys
import difflib
import subprocess
import argparse
import shutil
import tomllib
import git
from git import InvalidGitRepositoryError
from questionary import Choice, Separator, select
from packaging import version

def get_sorted_tags(repo):
    """有効なバージョンタグを取得し、新しい順にソートして返す"""
    assert version is not None
    all_tags = [t.name for t in repo.tags]
    valid_tags = []
    for tag in all_tags:
        try:
            v = version.parse(tag)
            valid_tags.append((tag, v))
        except version.InvalidVersion:
            pass
    
    # バージョンオブジェクトでソート (降順)
    valid_tags.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in valid_tags]


def get_appropriate_install_command(repo_path):
    """
    適切なインストールコマンドをユーザーに選択させる。
    uvコマンドがインストールされている場合は、uvコマンドを優先的に選択肢に表示する。

    Args:
        repo_path: リポジトリのパス

    Returns:
        選択されたインストールコマンドの辞書、またはキャンセル時は空文字
        辞書の形式: {'type': 'uv'|'python', 'command': str, 'description': str}
    """
    # uvコマンドがインストールされているか確認
    uv_installed = shutil.which('uv') is not None

    # 現在実行されているPythonのパスを取得
    current_python = sys.executable

    # venvフォルダを探す
    venv_python = None
    search_path = os.path.abspath(repo_path)

    while search_path:
        for venv_name in ['.venv', 'venv']:
            venv_path = os.path.join(search_path, venv_name)
            if os.path.isdir(venv_path):
                # venvのフォルダかどうかを確認
                # Windowsの場合はScripts/python.exe、Unix系はbin/python
                if os.name == 'nt':  # Windows
                    python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
                else:  # Unix系
                    python_exe = os.path.join(venv_path, 'bin', 'python')

                if os.path.isfile(python_exe):
                    venv_python = python_exe
                    break

        if venv_python:
            break

        # 階層をひとつ上がる
        parent_path = os.path.dirname(search_path)
        if parent_path == search_path:  # ルートディレクトリに到達
            break
        search_path = parent_path

    # 選択肢の作成
    choices = []

    # uvコマンドがインストールされている場合は先頭に追加
    if uv_installed:
        choices.append(Choice(
            title="uv pip install",
            value={'type': 'uv', 'command': 'uv pip install', 'description': 'uv pip install'}
        ))
        # uv addはpyproject.tomlが存在する場合のみ追加
        pyproject_path = os.path.join(repo_path, 'pyproject.toml')
        if os.path.isfile(pyproject_path):
            choices.append(Choice(
                title="uv add",
                value={'type': 'uv', 'command': 'uv add', 'description': 'uv add'}
            ))
        choices.append(Separator())

    # Pythonパスを表示用に短縮
    def format_path(path):
        # パスを短く表示（例: C:\Users\...\.venv\Scripts\python.exe）
        if len(path) > 120:
            parts = os.path.normpath(path).split(os.sep)
            if len(parts) > 3:
                return os.path.join('...', *parts[-3:])
        return os.path.normpath(path)

    if venv_python and venv_python != current_python:
        choices.append(Choice(
            title=f"Current Python ({format_path(current_python)})",
            value={'type': 'python', 'command': current_python, 'description': f'Current Python ({format_path(current_python)})'}
        ))
        choices.append(Choice(
            title=f"venv ({format_path(venv_python)})",
            value={'type': 'python', 'command': venv_python, 'description': f'venv ({format_path(venv_python)})'}
        ))
    elif current_python:
        choices.append(Choice(
            title=f"Current Python ({format_path(current_python)})",
            value={'type': 'python', 'command': current_python, 'description': f'Current Python ({format_path(current_python)})'}
        ))

    choices.append(Separator())
    choices.append(Choice(title="Cancel", value=""))

    # questionaryで選択させる
    selection = select("Select install command:", choices=choices).ask()

    if selection == "":
        return ""

    return selection


def install_requirements(repo, requirements_path):
    """
    指定されたインストールコマンドでrequirements.txtをインストールする。

    Args:
        repo: Gitリポジトリオブジェクト
        requirements_path: requirements.txtのパス
    """
    install_cmd = get_appropriate_install_command(repo.working_tree_dir)
    if install_cmd:
        print(f"Installing requirements using: {install_cmd['description']}")
        try:
            if install_cmd['type'] == 'uv':
                if install_cmd['command'] == 'uv pip install':
                    # uv pip install -r requirements.txt
                    subprocess.run(
                        ['uv', 'pip', 'install', '-r', requirements_path],
                        check=True
                    )
                elif install_cmd['command'] == 'uv add':
                    # uv add -r requirements.txt
                    subprocess.run(
                        ['uv', 'add', '-r', requirements_path],
                        check=True
                    )
            else:
                # Pythonインタープリタを使用: python -m pip install -r requirements.txt
                subprocess.run(
                    [install_cmd['command'], "-m", "pip", "install", "-r", requirements_path],
                    check=True
                )
            print("Requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install requirements: {e}")
    else:
        print("Skipped: pip installation cancelled by user.")


def install_requirements_uv(repo):
    """
    uv syncを実行するか、requirements.txtを使用するか、キャンセルするかをユーザーに選択させる。

    Args:
        repo: Gitリポジトリオブジェクト

    Returns:
        str: 選択されたアクション ("sync", "requirements", または None)
    """
    choices = [
        Choice(title="uv sync", value="sync"),
        Choice(title="use requirements.txt in next task", value="requirements"),
        Separator(),
        Choice(title="Cancel", value="")
    ]

    selection = select("Select an action:", choices=choices).ask()

    if selection == "sync":
        print("Running uv sync...")
        try:
            subprocess.run(['uv', 'sync'], check=True)
            print("uv sync completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to run uv sync: {e}")
        return "sync"
    elif selection == "requirements":
        return "requirements"
    return None  # キャンセル


def perform_update(repo, selection, reset=False):
    """
    選択されたアクションを実行する

    Args:
        repo: Gitリポジトリオブジェクト
        selection: ユーザーが選択したアクションを含む辞書
        reset: Trueの場合、git reset --hardを使用する
    """
    if not selection:
        print("Cancelled.")
        return

    action = selection.get('action')
    target = selection.get('target')

    # --- pyproject.toml の変更を追跡する処理 ---
    before_deps = None
    pyproject_path = os.path.join(repo.working_tree_dir, 'pyproject.toml')
    uv_installed = shutil.which('uv') is not None
    if uv_installed and os.path.isfile(pyproject_path):
        try:
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)
                # dependenciesセクションを取得
                deps = data.get('project', {}).get('dependencies', [])
                # ソートして比較用に文字列化
                before_deps = sorted(deps)
        except Exception:
            pass # ファイルが読めなくても処理は続行

    # --- requirements.txt の変更を追跡する処理 ---
    before_reqs = []
    reqs_path = os.path.join(repo.working_tree_dir, 'requirements.txt')
    if os.path.exists(reqs_path):
        try:
            with open(reqs_path, 'r', encoding='utf-8') as f:
                before_reqs = f.readlines()
        except IOError:
            pass # ファイルが読めなくても処理は続行

    # --- Git操作の実行 ---
    if action == 'checkout':
        print(f"Checking out tag '{target}'...")
        if reset:
            repo.git.checkout(target)
            # タグの場合はそのまま、ブランチの場合はorigin/{target}にreset
            try:
                # targetがリモートブランチとして存在するか確認
                repo.git.fetch()
                repo.git.reset('--hard', f'origin/{target}')
            except Exception:
                # リモートブランチが存在しない場合はtargetそのものにreset
                repo.git.reset('--hard', target)
            print(f"Done: Reset to {target}.")
        else:
            repo.git.checkout(target)
            print(f"Done: Switched to {target}.")
    elif action == 'pull':
        print(f"Pulling branch '{target}'...")
        if reset:
            repo.git.fetch()
            repo.git.reset('--hard', f'origin/{target}')
            print("Done: Reset to the latest remote state.")
        else:
            repo.git.pull()
            print("Done: Updated to the latest state.")
    elif action == 'checkout_pull':
        print(f"Checking out and pulling branch '{target}'...")
        repo.git.checkout(target)
        if reset:
            repo.git.reset('--hard', f'origin/{target}')
            print(f"Done: Reset {target} to the latest remote state.")
        else:
            repo.git.pull()
            print(f"Done: Updated {target} to the latest state.")
    else:
        return # 未知のアクションやキャンセル

    # --- リポジトリのメンテナンス ---
    print("\nPerforming repository maintenance...")
    repo.git.gc('--auto')

    # --- pyproject.toml の変更を表示 ---
    pyproject_changed = False
    if before_deps is not None:
        after_deps = None
        try:
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)
                deps = data.get('project', {}).get('dependencies', [])
                after_deps = sorted(deps)
        except Exception:
            pass # ファイルが読めなくても比較は行う

        if after_deps is not None and before_deps != after_deps:
            pyproject_changed = True
            print("\n--- Changes in pyproject.toml (dependencies) ---")
            before_lines = [f"{dep}\n" for dep in before_deps]
            after_lines = [f"{dep}\n" for dep in after_deps]
            diff = difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile='before pyproject.toml',
                tofile='after pyproject.toml',
            )
            for line in diff:
                print(line, end='')
            print("------------------------------------")
            print("\nWould you like to run uv sync to update dependencies?")
            result = install_requirements_uv(repo)
            if result != "requirements":
                return

    # --- requirements.txt の変更を表示 ---
    after_reqs = []
    if os.path.exists(reqs_path):
        try:
            with open(reqs_path, 'r', encoding='utf-8') as f:
                after_reqs = f.readlines()
        except IOError:
            pass # ファイルが読めなくても比較は行う
    
    if before_reqs != after_reqs:
        print("\n--- Changes in requirements.txt ---")
        diff = difflib.unified_diff(
            before_reqs,
            after_reqs,
            fromfile='before requirements.txt',
            tofile='after requirements.txt',
        )
        for line in diff:
            print(line, end='')
        print("------------------------------------")
        print("\nWould you like to install the updated requirements.txt?")
        print("Please select the Python path suitable for your venv environment.")
        install_requirements(repo, reqs_path)

def has_remote_updates(repo_path="."):
    """
    リモートリポジトリに更新があるかどうかを確認し、(更新有無, 詳細情報) のタプルを返す。
    
    戻り値: (bool, dict)
    辞書は以下のキーを含む:
    - type: 更新の種類 ('branch', 'tag', 'default_branch')
    - current: 現在のバージョンまたはブランチ名
    - latest: 最新のバージョンまたはブランチ名
    - message: 人間が読める形式のメッセージ (例: "v1.0.0 -> v1.1.0")
    - behind_count: 遅れているコミット数 (ブランチの場合)
    """
    # Gitリポジトリかどうかを事前にチェック
    try:
        repo = git.Repo(repo_path)
    except InvalidGitRepositoryError:
        return False, {}
    except Exception:
        return False, {}

    try:
        origin = repo.remotes.origin
        origin.fetch(tags=True)

        # 1. ブランチの更新チェック
        if not repo.head.is_detached:
            active_branch = repo.active_branch
            tracking_branch = active_branch.tracking_branch()
            if tracking_branch:
                behind = sum(1 for c in repo.iter_commits(f'{active_branch.name}..{tracking_branch.name}'))
                if behind > 0:
                    return True, {
                        'type': 'branch',
                        'current': active_branch.name,
                        'latest': tracking_branch.name,
                        'behind_count': behind,
                        'message': f"{behind} commits behind"
                    }

        # 2. タグの更新チェック
        current_tags_str = repo.git.tag(points_at=repo.head.commit.hexsha)
        current_tags = current_tags_str.split('\n') if current_tags_str else []
        
        current_tag_name = None
        if current_tags:
            if not repo.head.is_detached and repo.active_branch.name in current_tags:
                current_tag_name = repo.active_branch.name
            else:
                current_tag_name = current_tags[0]

        sorted_tags = get_sorted_tags(repo)
        latest_tag = sorted_tags[0] if sorted_tags else None

        if latest_tag and current_tag_name:
            try:
                if version.parse(latest_tag) > version.parse(current_tag_name):
                    return True, {
                        'type': 'tag',
                        'current': current_tag_name,
                        'latest': latest_tag,
                        'message': f"{current_tag_name} -> {latest_tag}"
                    }
            except version.InvalidVersion:
                pass

        # 3. デフォルトブランチの更新チェック
        # git remote show origin の出力から HEAD branch を探す
        show_output = repo.git.remote("show", "origin")
        default_branch = None
        for line in show_output.splitlines():
            if "HEAD branch:" in line:
                default_branch = line.split("HEAD branch:")[1].strip()
                break
        
        if default_branch:
            remote_ref = f"origin/{default_branch}"
            try:
                behind = sum(1 for c in repo.iter_commits(f'HEAD..{remote_ref}'))
                if behind > 0:
                    return True, {
                        'type': 'default_branch',
                        'current': 'HEAD',
                        'latest': default_branch,
                        'behind_count': behind,
                        'message': f"{default_branch} is {behind} commits ahead"
                    }
            except Exception:
                pass

        return False, {}

    except Exception:
        return False, {}

def check_remote_updates(repo_path=".", reset=False):
    """
    リモートの更新を確認し、ユーザーに選択肢を提示する

    Args:
        repo_path: Gitリポジトリのパス
        reset: Trueの場合、git reset --hardを使用する
    """

    # Gitリポジトリかどうかを事前にチェック
    try:
        repo = git.Repo(repo_path)
    except InvalidGitRepositoryError:
        print(f"Error: '{repo_path}' is not a Git repository.")
        return
    except Exception as e:
        print(f"Error: Failed to access Git repository at '{repo_path}': {e}")
        return

    try:
        origin = repo.remotes.origin

        remote_url = origin.url.removesuffix('.git')
        print(f"Remote URL: {remote_url}")
        if reset:
            print("Reset mode is enabled.")
        print("Fetching latest info from remote (origin)...")
        origin.fetch(tags=True)
        
        # 現在のコミットに紐づくタグを取得
        # repo.tagsの参照が不完全な場合を考慮し、gitコマンドを直接実行してタグを取得する
        current_tags_str = repo.git.tag(points_at=repo.head.commit.hexsha)
        current_tags = current_tags_str.split('\n') if current_tags_str else []

        # ブランチ情報の取得
        active_branch = None
        tracking_branch = None
        if not repo.head.is_detached:
            active_branch = repo.active_branch
            tracking_branch = active_branch.tracking_branch()

        current_tag_name = None
        if current_tags:
            if active_branch:
                current_tag_name = active_branch.name
            else:
                current_tag_name = current_tags[0]
            print(f"Currently checked out tag: {current_tag_name}")

        # --- 選択肢の作成 ---
        choices = []

        # リモートのデフォルトブランチを特定して、最新を取得する選択肢を追加
        default_branch = None
        try:
            show_output = repo.git.remote("show", "origin")
            for line in show_output.splitlines():
                if "HEAD branch:" in line:
                    default_branch = line.split("HEAD branch:")[1].strip()
                    break
            if default_branch:
                # 現在のブランチがデフォルトブランチと同じ場合は表示しない
                if not active_branch or active_branch.name != default_branch:
                    choices.append(Choice(
                        title=f"★ Checkout and Pull latest remote ({default_branch})",
                        value={'action': 'checkout_pull', 'target': default_branch}
                    ))
        except Exception:
            pass

        sorted_tags = get_sorted_tags(repo)
        latest_tag = sorted_tags[0] if sorted_tags else None

        # 1. ブランチの更新 (Pull)
        if active_branch and tracking_branch:
            behind = sum(1 for c in repo.iter_commits(f'{active_branch.name}..{tracking_branch.name}'))
            if behind > 0 or reset:
                title = f"★ Pull {active_branch.name}"
                if behind > 0:
                    title += f" ({behind} commits behind)"
                choices.append(Choice(
                    title=title,
                    value={'action': 'pull', 'target': active_branch.name}
                ))
            else:
                print(f"Current branch '{active_branch.name}' is up to date.")

        # 2. 最新タグへの更新 (Checkout)
        if latest_tag:
            is_newer = False
            if current_tag_name:
                try:
                    if version.parse(latest_tag) > version.parse(current_tag_name):
                        is_newer = True
                except version.InvalidVersion:
                    pass
            
            # 最新タグを選択肢に追加
            suffix = " (Latest)" if is_newer else ""
            choices.append(Choice(
                title=f"{latest_tag}{suffix}",
                value={'action': 'checkout', 'target': latest_tag}
            ))

        # 3. その他のタグ (最大10個)
        for tag in sorted_tags[:10]:
            if tag == latest_tag: continue
            choices.append(Choice(title=tag, value={'action': 'checkout', 'target': tag}))

        if len(choices) == 0:
            print("No updates available.")
            return

        choices.append(Separator())
        choices.append(Choice(title="Cancel", value=""))

        selection = select("Select an action:", choices=choices).ask()
        if not selection:
            print("Cancelled.")
            return
        perform_update(repo, selection, reset=reset)

    except Exception as e:
        print(f"An error occurred: {e}")


def command_main():
    parser = argparse.ArgumentParser(
        description='Check and update Git repository from remote.'
    )
    parser.add_argument(
        'repo_path',
        nargs='?',
        default='.',
        help='Path to the Git repository (default: current directory)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Use git reset --hard instead of git checkout/pull'
    )
    args = parser.parse_args()

    check_remote_updates(args.repo_path, reset=args.reset)
    print("All operations have been completed.")


if __name__ == "__main__":
    command_main()
