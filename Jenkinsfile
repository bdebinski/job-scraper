pipeline {
    agent { label 'python-agent' }

    stages {
        stage('Install dependencies') {
            steps {
                sh 'pip install --upgrade pip'
                sh 'pip install pipenv'
                sh 'pipenv install --dev'
            }
        }

        stage('Run tests') {
            steps {
                sh 'pipenv run python -m pytest -v tests/'
            }
        }
    }
}