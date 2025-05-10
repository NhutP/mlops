pipeline {
    agent { label 'builtin' }
    parameters {
        string(name: 'BUILD_VERSION', defaultValue: '0.0.0', description: 'build version')
        string(name: 'EXPERIMENT_ID', defaultValue: '0000', description: 'katib experiment version')
    }

    stages {
        stage('build training image') {
            agent { label 'docker' }
            // environment{
            //     BUILD_VERSION = ${params.BUILD_VERSION}
            // }
            steps {
                sh 'echo $BUILD_VERSION'
                checkout scm
                sh 'docker build -t nhutp/train_xgboost_normal:latest ./model/train_xgboost'
                sh 'docker tag nhutp/train_xgboost_normal:latest nhutp/train_xgboost_normal:$BUILD_VERSION'
                sh 'docker push nhutp/train_xgboost_normal:latest'
            }
        }
        
        stage('Start training') {
            agent { label 'k8s_master' }
             environment {
                EXPERIMENT_ID = ${params.EXPERIMENT_ID}
            }
            steps {
                sh 'echo $EXPERIMENT_ID'
                checkout scm

                script {
                    def yamlTemplate = readFile 'jenkins/katib-experiment.yaml'
                    def replacedYaml = yamlTemplate
                        .replace('__EXPERIMENT_ID__', "${EXPERIMENT_ID}")

                    writeFile file: './k8s_manifest/generated-xg-boost-katib.yaml', text: replacedYaml
                }
                
                sh 'sudo kubectl apply -f ./k8s_manifest/xg_boost_train_normal_job.yaml'
            }
        }

    }
}