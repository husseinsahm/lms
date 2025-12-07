pipeline {
    agent any

    environment {
        DOCKERHUB = credentials('dockerhub-creds')
        AWS_CREDS = credentials('aws-creds')
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/husseinsahm/lms.git'
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t lms-app .'
            }
        }

        stage('Docker Push') {
            steps {
                sh "docker tag lms-app husseinsahm/lms:latest"
                sh "echo ${DOCKERHUB_PSW} | docker login -u ${DOCKERHUB_USR} --password-stdin"
                sh "docker push husseinsahm/lms:latest"
            }
        }

        stage('Deploy to EKS') {
            steps {
                sh """
                    export AWS_ACCESS_KEY_ID=${AWS_CREDS_USR}
                    export AWS_SECRET_ACCESS_KEY=${AWS_CREDS_PSW}
                    export AWS_DEFAULT_REGION=us-east-1
                """

                sh 'aws eks update-kubeconfig --region us-east-1 --name my-eks-cluster'
                sh 'kubectl apply -f k8s/deployment.yaml'
                sh 'kubectl apply -f k8s/service.yaml'
            }
        }
    }
}
