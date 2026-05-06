from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def input_page():
    return render_template('input.html')

@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'GET':
        return redirect(url_for('input_page'))

    if request.method == 'POST':
        result = dict()
        result['Name'] = request.form.get('name')
        result['StudentNumber'] = request.form.get('student_number')
        result['Gender'] = request.form.get('gender')
        result['Major'] = request.form.get('major')

        lang_list = request.form.getlist('languages')
        result['languages'] = ', '.join(lang_list)
        
        return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
