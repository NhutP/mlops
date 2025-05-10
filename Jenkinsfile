pipeline {
    agent { label 'builtin' }

    stages {
        stage('build training image') {
            agent { label 'docker' }
            environment{
                BUILD_VERSION = '1.0.0'
            }
            steps {
                checkout scm
                sh 'docker build -t nhutp/train_xgboost_normal:latest ./model/train_xgboost'
                sh 'docker tag nhutp/train_xgboost_normal:latest nhutp/train_xgboost_normal:$BUILD_VERSION'
                sh 'docker push nhutp/train_xgboost_normal:latest'
            }
        }
        
        stage('Start training') {
            agent { label 'k8s_master' }
            steps {
                checkout scm
                sh 'sudo kubectl apply -f ./k8s_manifest/xg_boost_train_normal_job.yaml'
            }
        }

    }
}