pipeline {
    agent { label 'python-agent' }

    environment {
        PIPENV_SYSTEM = '1'
        PIPENV_SKIP_LOCK = 'true'
    }

    stages {
        stage('Install dependencies') {
            steps {
                sh 'pipenv install --dev'
            }
        }

        stage('Run tests') {
            steps {
                sh 'xvfb-run python -m pytest --junitxml=reports/results.xml tests/'
            }
            post {
                always {
                    junit 'reports/results.xml'
                }
            }
        }
    }
}
