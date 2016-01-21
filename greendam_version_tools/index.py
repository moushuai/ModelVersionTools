#Author='MouShuai'

import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import time
from result_structure import Model
from xml.dom.minidom import Document
import xml
import xml.etree.ElementTree as ET
# Initialize the Flask application
app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'models/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_MODEL_EXTENSIONS'] = set(['caffemodel', 'zip', 'tar'])
app.config['ALLOWED_RESULT_EXTENSIONS'] = set(['csv', 'txt'])
# This is the path to the processed result files
RESULT_FOLDER = 'result_folder'
ZIP_FOLDER = 'zip_folder'
LABEL = ['normal', 'porn', 'sexy']
XML_File = 'model.xml'


# For a given file, return whether it's an allowed type or not
def allowed_model_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_MODEL_EXTENSIONS']


def allowed_result_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_RESULT_EXTENSIONS']


def mkdir(path):
    path = path.strip()
    path = path.rstrip('\\')
    is_exists = os.path.exists(path)
    if is_exists is not True:
        print path
        os.makedirs(path)
    else:
        print('exists!')


def get_node_text(node):
    nodelist = node.childNodes
    result = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            result.append(node.data)
    return ''.join(result)


def create_model_version_xml(version, model_name, data_description, std_val_result_file):
    doc = Document()
    model = doc.createElement('Model')
    model.setAttribute('name', "greendam")
    # model.setAttribute('xsi:noNamespaceSchemaLocation', 'Model.xsd')
    doc.appendChild(model)
    version_node = doc.createElement('Version')
    version_node_text = doc.createTextNode(version)
    version_node.appendChild(version_node_text)
    model.appendChild(version_node)
    path_node = doc.createElement('Path')
    path_node_text = doc.createTextNode(os.path.join(version, model_name))
    path_node.appendChild(path_node_text)
    model.appendChild(path_node)
    date_node = doc.createElement('Date')
    timestamp = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    date_node_text = doc.createTextNode(timestamp)
    date_node.appendChild(date_node_text)
    model.appendChild(date_node)
    training_data_node = doc.createElement('Data')
    training_data_node_text = doc.createTextNode(data_description)
    training_data_node.appendChild(training_data_node_text)
    model.appendChild(training_data_node)
    std_result_node = doc.createElement('StdPerformance')
    with open(std_val_result_file) as fh:
        lines = fh.readlines()
        for line in lines:
            label_node = doc.createElement('Label')
            results = line.strip().split(' ')
            if results.__len__() > 1:
                for result in results:
                    result_node = doc.createElement('Result')
                    result_node_text = doc.createTextNode(result)
                    result_node.appendChild(result_node_text)
                    label_node.appendChild(result_node)
                std_result_node.appendChild(label_node)
            else:
                accuracy_node = doc.createElement('Accuracy')
                accuracy_node_text = doc.createTextNode(results[0])
                accuracy_node.appendChild(accuracy_node_text)
                std_result_node.appendChild(accuracy_node)
        fh.close()
    model.appendChild(std_result_node)
    apd_result_node = doc.createElement('ApdPerformance')
    model.appendChild(apd_result_node)
    with open(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], version), XML_File), 'w') as fw:
        fw.write(doc.toprettyxml())
        fw.close()


def add_node_to_xml(xml_path, distribution_file_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    apd_result_node = root.find('ApdPerformance')
    x = 0
    for i in apd_result_node:
        if i.tag != 'Performance':
            x += 1
        else:
            break
    performance_node = ET.Element('Performance')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    performance_node.set('time', timestamp)
    with open(distribution_file_path, 'r') as fh:
        lines = fh.readlines()

        for line in lines:
            results = line.strip().split(' ')
            if results.__len__() > 1:
                label_node = ET.SubElement(performance_node, 'Label')
                for result in results:
                    result_node = ET.SubElement(label_node, 'Result')
                    result_node.text = result
            else:
                accuracy_node = ET.SubElement(performance_node, 'Accuracy')
                accuracy_node.text = results[0]
    apd_result_node.insert(x, performance_node)
    fh.close()
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    # with open(xml_path, 'w') as fw:
    #     fw.write()


def get_model_by_version(version):
    model = Model()
    version_path = os.path.join(app.config['UPLOAD_FOLDER'], version)
    xml_path = os.path.join(version_path, XML_File).replace('\\', '/')
    print(xml_path)
    doc = xml.dom.minidom.parse(xml_path).documentElement
    version_node = doc.getElementsByTagName('Version')[0]
    path_node = doc.getElementsByTagName('Path')[0]
    date_node = doc.getElementsByTagName('Date')[0]
    data_node = doc.getElementsByTagName('Data')[0]
    model.version = get_node_text(version_node)
    model.path = get_node_text(path_node)
    model.date = get_node_text(date_node)
    model.data_description = get_node_text(data_node)
    std_performance_node = doc.getElementsByTagName('StdPerformance')[0]
    labels = std_performance_node.getElementsByTagName('Label')

    for label in labels:
        results = label.getElementsByTagName('Result')
        result_list = []
        for result in results:
            result_list.append(get_node_text(result))
        model.std_result.append(result_list)
    std_accuracy_node = std_performance_node.getElementsByTagName('Accuracy')[0]
    model.std_accuracy = get_node_text(std_accuracy_node)

    performances = doc.getElementsByTagName('Performance')
    for performance in performances:
        model.update_times.append(performance.getAttribute('time'))
        labels = performance.getElementsByTagName('Label')
        label_list = []
        for label in labels:
            results = label.getElementsByTagName('Result')
            result_list = []
            for result in results:
                result_list.append(get_node_text(result))
            label_list.append(result_list)
        model.distribution_list.append(label_list)
        apd_accuracy_node = performance.getElementsByTagName('Accuracy')[0]
        model.accuracy_list.append(get_node_text(apd_accuracy_node))
    return model


# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/model_list')
def model_show_in_list():
    version_list = os.listdir(app.config['UPLOAD_FOLDER'])
    model_list = []
    has_model = True
    for version in version_list:
        model = get_model_by_version(version)
        model_list.append(model)
    if model_list.__len__() > 0:
        model_list.sort(key=lambda x: x.date, reverse=True)
    else:
        has_model = False
    return render_template('model_list.html', model_list=model_list, has_model=has_model)


@app.route('/<version>')
def model_in_details(version):
    model = get_model_by_version(version)
    has_distribution = True
    if model.distribution_list.__len__() == 0:
        has_distribution = False
    print(model.distribution_list[0][0].__len__())
    return render_template('model.html', model=model, labels=LABEL, has_distribution=has_distribution)


@app.route('/update', methods=['POST'])
def update():
    version = request.form.get('ModelVersion')
    append_result_file = request.files['AppendResultFile']
    print(version)
    print(append_result_file.filename)
    if append_result_file and allowed_result_file(append_result_file.filename) and version is not None:
        append_result_name = secure_filename(append_result_file.filename)
        append_result_save_path = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], version), append_result_name)
        append_result_file.save(append_result_save_path)
        xml_path = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], version), XML_File)
        add_node_to_xml(xml_path, append_result_save_path)
    model = get_model_by_version(version)
    print(model.distribution_list[0].__len__())
    return render_template('model.html', model=model, labels=LABEL, has_distribution=True)


@app.route('/upload_append_data_result')
def upload_append_data_result():
    version_list = os.listdir(app.config['UPLOAD_FOLDER'])
    has_model = True
    print(version_list.__len__())
    if version_list.__len__() == 0:
        has_model = False
    return render_template('update.html', version_list=version_list, has_model=has_model)


# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded files
    model_file = request.files['ModelFile']
    model_version= request.form.get('ModelVersion')
    data_description = request.form.get('DataDescription')
    distribution_file = request.files['DistributionFile']
    print model_file.filename
    print model_version
    print data_description
    print distribution_file.filename
    if model_file and allowed_model_file(model_file.filename) and distribution_file:
        model_name = secure_filename(model_file.filename)
        mkdir(os.path.join(app.config['UPLOAD_FOLDER'], model_version))
        model_file_path = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], model_version), model_name)
        model_file.save(model_file_path)
        distribution_file_name = secure_filename(distribution_file.filename)
        distribution_file_path = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], model_version),
                                              distribution_file_name)
        distribution_file.save(distribution_file_path)
        version_path = os.path.join(app.config['UPLOAD_FOLDER'], model_version)
        mkdir(version_path)
        # mkdir(os.path.join(version_path, XML_File))
        create_model_version_xml(model_version, model_name, data_description, distribution_file_path)
        os.remove(distribution_file_path)
        model = get_model_by_version(model_version)
    return render_template('model.html', model=model, labels=LABEL, has_distribution=False)


@app.route('/uploads/<path:model_path>', methods=['GET', 'POST'])
def download(model_path):
    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], filename=model_path)


# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
# http://www.sharejs.com
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/data/<filename>')
def data(filename):
    return send_from_directory('data', filename)

if __name__ == '__main__':
    app.run(
        debug=True
    )

