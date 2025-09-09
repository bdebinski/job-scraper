pipeline {
    agent { label 'python-agent' }
    stages {
        stage('Uruchom testy') {
            steps {
                sh 'python3 --version'
                sh 'pytest tests/'
            }
        }
    }
}