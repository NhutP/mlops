pipeline {
    agent { label 'builtin' }

    environment {
        KUBECONFIG = "${params.KUBE_CONFIG}"  // Specify the path to your kubeconfig file
    }

    parameters {
        string(name: 'BUILD_VERSION', defaultValue: '0.0.0', description: 'build version')
        string(name: 'EXPERIMENT_ID', defaultValue: '0000', description: 'katib experiment version')
    }

    stages {
        stage('build training image') {
            agent { label 'docker' }

            steps {
                checkout scm
                sh 'docker build -t nhutp/train_xgboost_normal:latest ./model/train_xgboost'
                sh 'docker tag nhutp/train_xgboost_normal:latest nhutp/train_xgboost_normal:$BUILD_VERSION'
                sh 'docker push nhutp/train_xgboost_normal:latest'
            }
        }
        
        stage('Start training') {
             environment {
                EXPERIMENT_ID = "${params.EXPERIMENT_ID}"
            }
            steps {
                checkout scm
                sh 'whoami'

                script {
                    def yamlTemplate = readFile './k8s_manifest/xg_boost_train_normal_job.yaml'
                    def replacedYaml = yamlTemplate
                        .replace('__EXPERIMENT_ID__', "${EXPERIMENT_ID}")

                    writeFile file: "./k8s_manifest/generated-xg-boost-katib-${params.EXPERIMENT_ID}.yaml", text: replacedYaml
                }
                
                sh "kubectl apply -f ./k8s_manifest/generated-xg-boost-katib-${env.EXPERIMENT_ID}.yaml"
            }
        }
    
        stage('Wait for Katib Completion') {
            steps {
                sh '''
                # Wait until experiment finished (simplified polling)
                for i in {1..600}; do
                    status=$(kubectl get experiment xgboost-hpo-${EXPERIMENT_ID} -n kubeflow -o jsonpath='{.status.conditions[0].type}')
                    if [ "$status" = "Succeeded" ]; then
                        break
                    fi
                    sleep 10
                done
                '''
            }
        }

        stage('Get Best Hyperparameters') {
            steps {
                script {
                    def bestParamsJson = sh(script: "kubectl get experiment xgboost-hpo-${EXPERIMENT_ID} -n kubeflow -o json | jq '.status.currentOptimalTrial.parameterAssignments'", returnStdout: true).trim()
                    def bestParams = readJSON text: bestParamsJson

                    env.LEARNING_RATE = bestParams.find { it.name == "LEARNING_RATE" }.value
                    env.MAX_DEPTH     = bestParams.find { it.name == "MAX_DEPTH" }.value
                    env.NUM_ROUND     = bestParams.find { it.name == "NUM_ROUND" }.value
                }

                script {
                  
                    def jobYaml = readFile('final_training_job.yaml')

                    jobYaml = jobYaml.replaceAll("__OPT_LEARNING_RATE__", env.LEARNING_RATE)
                    jobYaml = jobYaml.replaceAll("__OPT_MAX_DEPTH__", env.MAX_DEPTH)
                    jobYaml = jobYaml.replaceAll("__OPT_NUM_ROUND__", env.NUM_ROUND)
                    jobYaml = jobYaml.replaceAll("__MODEL_VERSION__", "${params.EXPERIMENT_ID}")
                    jobYaml = jobYaml.replaceAll("__EXPERIMENT_ID__", "${EXPERIMENT_ID}")

                    writeFile file: 'generated_final_training_job_${params.EXPERIMENT_ID}.yaml', text: jobYaml
                }

                sh "kubectl apply -f ./k8s_manifest/generated-xg-boost-katib-${env.EXPERIMENT_ID}.yaml"
            }
        }
    }
}