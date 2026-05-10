from flask import Flask, render_template, redirect, url_for, session, abort, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import os
import json
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DATA_FILE = os.path.join(app.root_path, "data", "members.json")

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_PORTFOLIO_EXTENSIONS = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "zip",
    "png", "jpg", "jpeg", "gif", "webp"
}
PREDEFINED_LANGUAGES = {"Python", "Java", "C/C++", "HTML/CSS", "SQL"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def load_root_data():
    # members.json에서 ROOT 팀 전체 데이터를 불러오기
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_root_team():
    # ROOT 팀 소개 정보 반환
    data = load_root_data()
    return data.get("team", {})


def load_root_members():
    # ROOT 팀원 목록 반환
    data = load_root_data()
    return data.get("members", [])


def get_root_member_by_id(member_id):
    members = load_root_members()

    for member in members:
        if int(member.get("id")) == member_id:
            return member

    return None


def init_generated_team():
    if "generated_team" not in session:
        session["generated_team"] = {
            "team_name": "",
            "team_intro": "",
            "team_image": "images/default-team.png",
            "members": [],
            "next_member_id": 1000
        }


def get_generated_team():
    init_generated_team()
    return session["generated_team"]


def save_generated_team(team):
    session["generated_team"] = team
    session.modified = True


def get_generated_member_by_id(member_id):
    team = get_generated_team()

    for member in team.get("members", []):
        if int(member.get("id")) == member_id:
            return member

    return None

def allowed_file(filename, allowed_extensions=ALLOWED_EXTENSIONS):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, default_path):
    if file is None or file.filename == "":
        return default_path

    if not allowed_file(file.filename):
        return default_path

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    ext = file.filename.rsplit(".", 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
    file.save(save_path)

    return f"uploads/{new_filename}"


def save_uploaded_asset(file, default_path="", default_name="", subfolder="", allowed_extensions=None):
    if file is None or file.filename == "":
        return default_path, default_name

    allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS
    if not allowed_file(file.filename, allowed_extensions):
        return default_path, default_name

    upload_folder = os.path.join(app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_folder, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    save_path = os.path.join(upload_folder, new_filename)
    file.save(save_path)

    upload_path = f"uploads/{new_filename}" if not subfolder else f"uploads/{subfolder}/{new_filename}"
    return upload_path, file.filename


@app.route("/")
def index():
    # ROOT 팀 소개 메인 페이지
    team = load_root_team()
    members = load_root_members()

    return render_template(
        "index.html",
        team=team,
        members=members
    )

@app.route("/input")
def input_page():
    # 팀페이지 제작 및 팀원 입력/수정 페이지
    # /input 새 팀원 입력 모드
    # /input?member_id=1000 기존 팀원 수정 모드
    team = get_generated_team()
    member_id = request.args.get("member_id", type=int)

    member = None
    member_custom_language = ""
    if member_id:
        member = get_generated_member_by_id(member_id)

        if member is None:
            abort(404)

        custom_languages = [
            language
            for language in member.get("languages", [])
            if language not in PREDEFINED_LANGUAGES
        ]
        member_custom_language = ", ".join(custom_languages)

    return render_template(
        "input.html",
        team=team,
        member=member,
        member_custom_language=member_custom_language,
        member_count=len(team.get("members", []))
    )


@app.route("/member/update", methods=["POST"])
def update_member():
    """
    팀 정보 저장 + 팀원 추가 + 팀원 수정 처리
    """
    team = get_generated_team()

    # 팀 정보 저장
    team["team_name"] = request.form.get("team_name", team.get("team_name", "")).strip()
    team["team_intro"] = request.form.get("team_intro", team.get("team_intro", "")).strip()

    team_image = request.files.get("team_image")
    team["team_image"] = save_uploaded_file(
        team_image,
        team.get("team_image", "images/default-team.png")
    )

    action = request.form.get("action", "add")
    member_id = request.form.get("member_id", type=int)  # 수정 여부 판단용


    # 이름 없으면 무시
    name = request.form.get("name", "").strip()

    if action == "make" and not member_id and not name:
        save_generated_team(team)
        return redirect(url_for("result"))

    if not name:
        save_generated_team(team)
        return redirect(url_for("input_page"))

    profile_image = request.files.get("profile_image")
    github_id = request.form.get("github", "").strip()
    sns_id = request.form.get("sns", "").strip()

    github_url = f"https://github.com/{github_id}" if github_id else ""
    sns_url = f"https://instagram.com/{sns_id}" if sns_id else ""
    portfolio_link = request.form.get("portfolio_link", "").strip()
    portfolio_file = request.files.get("portfolio_file")
    portfolio_file_path, portfolio_file_name = save_uploaded_asset(
        portfolio_file,
        request.form.get("portfolio_file_path", "").strip(),
        request.form.get("portfolio_file_name", "").strip(),
        subfolder="portfolio",
        allowed_extensions=ALLOWED_PORTFOLIO_EXTENSIONS
    )

    portfolio = []
    portfolio_titles = request.form.getlist("portfolio_title")
    portfolio_starts = request.form.getlist("portfolio_start_date")
    portfolio_ends = request.form.getlist("portfolio_end_date")
    portfolio_roles = request.form.getlist("portfolio_role")
    portfolio_descs = request.form.getlist("portfolio_desc")

    for title, start, end, role, desc in zip(
        portfolio_titles,
        portfolio_starts,
        portfolio_ends,
        portfolio_roles,
        portfolio_descs
    ):
        title = title.strip()
        start = start.strip()
        end = end.strip()
        role = role.strip()
        desc = desc.strip()

        if title or start or end or role or desc:
            portfolio.append({
                "title": title,
                "period": f"{start} ~ {end}",
                "role": role,
                "desc": desc
            })

    languages = request.form.getlist("languages")

    language_etc = request.form.get("language_etc", "").strip()
    language_etc_checked = request.form.get("language_etc_check")

    if language_etc_checked and language_etc:
        languages.append(language_etc)

    # 공통 member_data
    member_data = {
        "name": name,
        "student_number": request.form.get("student_number", "").strip(),
        "major": request.form.get("major", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip(),
        "gender": request.form.get("gender", "").strip(),
        "role": request.form.get("role", "").strip(),
        "languages": languages,
        "github": github_url,
        "sns": sns_url,
        "intro": request.form.get("intro", "").strip(),
        "portfolio_link": portfolio_link,
        "portfolio_file": portfolio_file_path,
        "portfolio_file_name": portfolio_file_name,
        "portfolio": portfolio
    }

    # 수정 로직 (member_id 존재하면 수정)
    if member_id:
        for idx, member in enumerate(team.get("members", [])):
            if int(member.get("id")) == member_id:
                old_image = member.get("image", "images/default.png")

                member_data["id"] = member_id
                member_data["image"] = save_uploaded_file(profile_image, old_image)

                team["members"][idx] = member_data
                save_generated_team(team)

                return redirect(url_for("member_detail", member_id=member_id))

        abort(404)

    # 새 팀원 추가
    if len(team.get("members", [])) >= 4:
        save_generated_team(team)
        return redirect(url_for("input_page"))

    new_id = team.get("next_member_id", 1000)
    team["next_member_id"] = new_id + 1

    member_data["id"] = new_id
    member_data["image"] = save_uploaded_file(profile_image, "images/default.png")

    team["members"].append(member_data)
    save_generated_team(team)

    if action == "make":
        return redirect(url_for("result"))

    return redirect(url_for("input_page"))

@app.route("/result")
def result():
    # 생성된 팀페이지 결과 화면
    team = get_generated_team()

    return render_template(
        "result.html",
        team=team,
        members=team.get("members", [])
    )


@app.route("/members/<int:member_id>")
def member_detail(member_id):
    root_member = get_root_member_by_id(member_id)

    if root_member:
        return render_template(
            "member_detail.html",
            member=root_member,
            is_root_member=True
        )

    generated_member = get_generated_member_by_id(member_id)

    if generated_member:
        return render_template(
            "member_detail.html",
            member=generated_member,
            is_root_member=False
        )

    abort(404)

@app.route("/contact")
def contact():
    # 비상연락망 페이지
    members = load_root_members()

    return render_template(
        "contact.html",
        members=members
    )
@app.route("/reset")
def reset_team():
    session.pop("generated_team", None)
    return redirect(url_for("input_page"))

# 게시글 CRUD =====================================================================

def get_posts():
    with open('data/posts.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/board')
def board_list():
    posts = get_posts() 
    return render_template('board/post_list.html', posts=posts)

@app.route('/board/write')
def board_write():
    return render_template('board/post_form.html', post=None)

@app.route('/board/<int:post_id>')
def board_detail(post_id):
    with open('data/posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post: abort(404)

    curr_idx = posts.index(post)
    prev_post = posts[curr_idx - 1] if curr_idx > 0 else None
    next_post = posts[curr_idx + 1] if curr_idx < len(posts) - 1 else None

    try:
        with open('data/comments.json', 'r', encoding='utf-8') as f:
            all_comments = json.load(f)
    except FileNotFoundError:
        all_comments = []
    
    post_comments = [c for c in all_comments if c['post_id'] == post_id]

    return render_template('board/post_detail.html', 
                           post=post, prev_id=prev_post['id'] if prev_post else None,
                           next_id=next_post['id'] if next_post else None,
                           comments=post_comments)

@app.route('/board/<int:post_id>/edit')
def board_edit(post_id):
    # 수정 화면 보여주기 (GET)
    with open('data/posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post: abort(404)
    return render_template('board/post_form.html', post=post)

# 통합된 라우트 1: 게시글 생성/수정/삭제를 한번에 처리
@app.route('/board/update', methods=['POST'])
def board_update():
    action = request.form.get('action', 'add') # add, edit, delete 중 하나
    post_id = request.form.get('post_id', type=int)
    input_pw = request.form.get('password', '').strip()

    try:
        with open('data/posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except FileNotFoundError:
        posts = []

    # 1. 새 글 작성
    if action == 'add':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()

        if not all([title, author, input_pw, content]):
            return "<script>alert('모든 항목을 입력해야 합니다.'); history.back();</script>"
        if not (input_pw.isdigit() and len(input_pw) == 4):
            return "<script>alert('비밀번호는 숫자 4자리여야 합니다.'); history.back();</script>"

        new_post = {
            "id": posts[-1]['id'] + 1 if posts else 1,
            "title": title, "author": author, "password": input_pw,
            "content": content, "date": datetime.now().strftime("%Y.%m.%d")
        }
        posts.append(new_post)
        with open('data/posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        return redirect('/board')

    # 2. 수정/삭제 공통 (기존 데이터 검증)
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post: abort(404)
    
    if str(input_pw) != str(post['password']):
        return "<script>alert('비밀번호가 일치하지 않습니다.'); history.back();</script>"

    # 2-1. 수정 처리
    if action == 'edit':
        new_title = request.form.get('title', '').strip()
        new_content = request.form.get('content', '').strip()
        if not new_title or not new_content:
            return "<script>alert('제목과 내용을 모두 입력해주세요.'); history.back();</script>"

        post['title'] = new_title
        post['content'] = new_content
        with open('data/posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        return redirect(f'/board/{post_id}')
        
    # 2-2. 삭제 처리
    elif action == 'delete':
        # 1) 게시글 삭제
        posts.remove(post)
        with open('data/posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

        # 2) 연쇄 삭제: 해당 게시글에 달린 댓글도 모두 삭제
        try:
            with open('data/comments.json', 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
            
            filtered_comments = [c for c in all_comments if c['post_id'] != post_id]
            
            with open('data/comments.json', 'w', encoding='utf-8') as f:
                json.dump(filtered_comments, f, indent=2, ensure_ascii=False)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return redirect('/board')

# 댓글 CRUD =====================================================================

@app.route('/comments/<int:comment_id>/edit')
def comment_edit_view(comment_id):
    with open('data/comments.json', 'r', encoding='utf-8') as f:
        comments = json.load(f)
    comment = next((c for c in comments if c['id'] == comment_id), None)
    if not comment: abort(404)
    return redirect(url_for('board_detail', post_id=comment['post_id'], edit_comment_id=comment_id) + f"#comment-{comment_id}")

# 통합된 라우트 2: 댓글 생성/수정/삭제를 한번에 처리
@app.route('/comment/update', methods=['POST'])
def comment_update():
    action = request.form.get('action', 'add')
    post_id = request.form.get('post_id', type=int)
    comment_id = request.form.get('comment_id', type=int)
    input_pw = request.form.get('password', '').strip()

    try:
        with open('data/comments.json', 'r', encoding='utf-8') as f:
            comments = json.load(f)
    except FileNotFoundError:
        comments = []

    # 1. 새 댓글 작성
    if action == 'add':
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()
        if not all([author, input_pw, content]):
            return "<script>alert('모든 항목을 입력해주세요.'); history.back();</script>"

        new_comment = {
            "id": int(datetime.now().timestamp() * 1000), "post_id": post_id,
            "author": author, "password": input_pw, "content": content,
            "date": datetime.now().strftime("%Y.%m.%d %H:%M")
        }
        comments.append(new_comment)
        with open('data/comments.json', 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
        return redirect(f'/board/{post_id}')

    # 2. 수정/삭제 공통
    comment = next((c for c in comments if c['id'] == comment_id), None)
    if not comment: abort(404)
    if str(input_pw) != str(comment['password']):
        return "<script>alert('비밀번호가 틀렸습니다.'); history.back();</script>"

    # 2-1. 수정 처리
    if action == 'edit':
        comment['author'] = request.form.get('author', '').strip()
        comment['content'] = request.form.get('content', '').strip()
        with open('data/comments.json', 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
        return redirect(f'/board/{comment["post_id"]}#comment-{comment_id}')

    # 2-2. 삭제 처리
    elif action == 'delete':
        target_post_id = comment['post_id']
        comments.remove(comment)
        with open('data/comments.json', 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
        return redirect(f'/board/{target_post_id}')


if __name__ == "__main__":
    app.run(debug=True)