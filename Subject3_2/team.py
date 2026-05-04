from flask import Flask, render_template, redirect, url_for, session, abort, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import json
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DATA_FILE = os.path.join(app.root_path, "data", "members.json")

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
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

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, default_path):
    if file is None or file.filename == "":
        return default_path

    if not allowed_file(file.filename):
        return default_path

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
    file.save(save_path)

    return f"uploads/{new_filename}"


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
    portfolio_title = request.form.get("portfolio_title", "").strip()
    portfolio_start = request.form.get("portfolio_start_date", "").strip()
    portfolio_end = request.form.get("portfolio_end_date", "").strip()
    portfolio_role = request.form.get("portfolio_role", "").strip()
    portfolio_desc = request.form.get("portfolio_desc", "").strip()

    portfolio = []
    github_id = request.form.get("github", "").strip()
    sns_id = request.form.get("sns", "").strip()

    github_url = f"https://github.com/{github_id}" if github_id else ""
    sns_url = f"https://instagram.com/{sns_id}" if sns_id else ""

    if portfolio_title or portfolio_start or portfolio_end or portfolio_role or portfolio_desc:
        portfolio.append({
            "title": portfolio_title,
            "period": f"{portfolio_start} ~ {portfolio_end}",
            "role": portfolio_role,
            "desc": portfolio_desc
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

if __name__ == "__main__":
    app.run(debug=True)
