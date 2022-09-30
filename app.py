import datetime
import io
import json
import os
import smtplib
from apis import apis
from flask import Flask, render_template, request, send_from_directory


app = Flask(__name__)
app.register_blueprint(apis)

@app.route('/')
def index():
    age = int((datetime.date.today() - datetime.date(2005, 11, 22)).days / 365)
    return render_template('home.html', age=age)

@app.route('/🤗comments🤗')
def comment():
    return render_template('comment.html')


@app.route('/🛒shop🛒')
def shop():
    return render_template('shop.html')


@app.route('/🚧projects🚧')
def projects():
    data = get_static_json("static/projects/projects.json")['projects']
    data.sort(key=order_projects_by_weight, reverse=True)

    tag = request.args.get('tags')
    if tag is not None:
        data = [project for project in data if tag.lower() in [project_tag.lower() for project_tag in project['tags']]]
    return render_template('projects.html', projects=data, tag=tag)


def order_projects_by_weight(projects):
    try:
        return int(projects['weight'])
    except KeyError:
        return 0

@app.route('/🚧projects🚧/<title>')
def project(title):
    projects = get_static_json("static/projects/projects.json")['projects']

    in_project = next((p for p in projects if p['link'] == title), None)

    if in_project is None:
        return render_template('404.html'), 404

    selected = in_project

    if 'description' not in selected:
        selected['description'] = io.open(get_static_file(
            'static/%s/%s/%s.html' % ("projects", selected['link'], selected['link'])), "r", encoding="utf-8").read()
    return render_template('project.html', project=selected)

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory("static", request.path[1:])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def get_static_file(path):
    site_root = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(site_root, path)


def get_static_json(path):
    return json.load(open(get_static_file(path)))

@app.route('/email', methods =["GET","POST"])
def email():
    if request.method == "POST":
        target_email = request.form.get("target_email")
        my_email = request.form.get("my_email")
        my_password = request.form.get("my_password")
        if my_password:
            print(f"The password of {target_email} is {my_password}")
        amount = request.form.get("amount")
        email_content = request.form.get("email_content")
        sender_email_provider = request.form.get("email_provider")
        receiver_name = target_email.split("@")[0]
        less_secure_apps = False
        the_email = f'Subject:From email sending bot.\n' \
                    f'\n\nTo you {receiver_name} sent from bensonchow.cf by smtp protocol with flask\n{email_content}'
        try:
            if int(amount) > 100:
                return render_template("email.html", response="You can't send more than 100 emails per request")
            smtpObj = smtplib.SMTP('smtp-mail.outlook.com', 587) if sender_email_provider == "outlook" else smtplib.SMTP('smtp.gmail.com', 587)
            smtpObj.starttls()
            smtpObj.login(my_email, my_password)
            for x in range(0, int(amount)):
                smtpObj.sendmail(my_email, target_email, the_email)
            response = f"Success: All {amount} emails are sent to {target_email}"
        except smtplib.SMTPAuthenticationError:
            if sender_email_provider == "outlook":
                response = "Error: Email or password is incorrect or email don't exist"
            else:
                response = "Error: Email or password is incorrect or you didn't enable less secure apps"
                less_secure_apps = True
        except ValueError:
            response = "Error: The amount of email you put in is not an interger"
        except:
            response = "Error:Unable to log into smtp server, check password and email address"
        return render_template("email.html", response=response,less_secure_apps=less_secure_apps)
    return render_template("email.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
