Model Version Management Tool
=================================
This is a web tool for model version management

### Deployment
		1.mkdir <application folder>
		
		2.cd <application folder>
		
		3.venv ¨Cs <virtual env path>
		
		4.activate the virtual environment:
			source <virtual env path>/bin/activate
		  
		5.write a wsgi script:
			from app import app
			
			if __name__ == ¡®__main__¡¯:

					app.run()
		
		6.To run uWSGI to start serving the application from wsgi.py, run the following:
			uwsgi --socket 127.0.0.1:5082 -w WSGI:app

### Tips
		1.All the upload files will be stored in folder /models
		