pipeline {
    agent { label 'python-agent' }

    stages {
        stage('Install dependencies') {
            steps {
                sh 'pip install --upgrade pip'
                sh 'pip install pipenv'
                sh 'pipenv install --dev'
                sh 'pipenv run python -m playwright install --with-deps'
            }
        }

        stage('Run tests') {
            steps {
                sh 'pipenv run pytest -v tests/'
            }
        }
    }
}