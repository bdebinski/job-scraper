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
                sh 'pipenv run python -m pytest --junitxml=reports/results.xml tests/'
            }
            post {
                always {
                    junit 'reports/results.xml'
                }
            }
        }
    }
}