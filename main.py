import crud
import random
import flask
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)
SURVEY_DB = 'daiict_survey.sqlite3'


@app.route('/')
def index():
    return redirect(url_for('provide_ssId'))


@app.route('/survey_finished')
def survey_finished():
    return render_template("survey_finished.html")


@app.route('/invalid_ssId')
def invalid_ssId():
    return render_template("invalid_ssId.html")


@app.route('/provide_ssId', methods=['GET', 'POST'])
def provide_ssId():
    if request.method == 'GET':
        return render_template("index.html")
    if request.method == 'POST':
        ssId = request.form.get('ssId')

        # validate author:
        conn = crud.create_connection(SURVEY_DB)
        if (author_pk:=crud.validate_author(conn, ssId)) is not None:
            return redirect(url_for('reviewer_matchmaking', author_pk=author_pk))
        return redirect(url_for('invalid_ssId'))


@app.route('/surveys/reviewer_matchmaking/<author_pk>', methods=['GET', 'POST'])
def reviewer_matchmaking(author_pk):
    conn = crud.create_connection(SURVEY_DB)
    author_data = crud.get_author_data(conn, author_pk)

    if author_data == []:
        return redirect(url_for('survey_finished'))

    random.Random(4).shuffle(author_data) # prevents second shuffle during POST

    data_dict = {"author_pk": author_pk, "data_length": len(author_data), "data": author_data}
    if request.method == 'GET':
        return render_template("main.html", lst=data_dict)
    if request.method == 'POST':
        # gender = request.form.get('gender')
        # occupation = request.form.get('occupation')

        responses = []
        for i in range(len(author_data)):
            responses.append(request.form.get(str(i)))

        crud.store_response(conn, data_dict, responses)

        if request.form.get('SubmitAndExit') is not None:
            return redirect(url_for('provide_ssId'))
        elif request.form.get('SubmitAndFillAgain') is not None:
            return redirect(url_for('reviewer_matchmaking', author_pk=author_pk))


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000, debug=True)
    app.run(host='0.0.0.0', port=81, debug=True)
