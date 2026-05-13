pipeline {
    agent any

    environment {
        CONFIG_FILE = 'pipeline.config'
        REGISTRY_CREDS = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY = 'registry-1.docker.io'
        VENV_PATH = 'venv'
    }

    stages {
        stage('checkout') {
            steps {
                checkout scm
                script {
                    // Parse pipeline.config (KEY=VALUE format)
                    def configLines = readFile(CONFIG_FILE).readLines()
                    def config = [:]
                    configLines.each { line ->
                        if (line && !line.trim().startsWith('#') && line.contains('=')) {
                            def parts = line.split('=', 2)
                            config[parts[0].trim()] = parts[1].trim()
                        }
                    }
                    env.DOCKER_IMAGE = config.DOCKER_IMAGE
                    env.DEPLOY_HOST = config.DEPLOY_HOST
                    env.DEPLOY_USER = config.DEPLOY_USER
                    env.DEPLOY_BRANCH = config.DEPLOY_BRANCH
                    env.CONTAINER_NAME = config.CONTAINER_NAME
                    
                    echo "✅ Config loaded:"
                    echo "   Image: ${DOCKER_IMAGE}"
                    echo "   Host: ${DEPLOY_HOST}"
                    echo "   Branch: ${DEPLOY_BRANCH}"
                    echo "   Container: ${CONTAINER_NAME}"
                }
            }
        }

        stage('setup') {
            steps {
                script {
                    echo "📦 Setting up Python environment..."
                    sh '''
                        # Create virtual environment
                        python3 -m venv ${VENV_PATH}
                        . ${VENV_PATH}/bin/activate
                        
                        # Upgrade pip and install dependencies
                        pip install --upgrade pip
                        if [ -f requirements.txt ]; then
                            echo "   Installing from requirements.txt..."
                            pip install -r requirements.txt
                        fi
                        
                        # Ensure test/quality tools are available
                        pip install --quiet pytest pytest-cov pytest-junit flake8
                    '''
                }
            }
        }

        stage('build') {
            steps {
                script {
                    echo "🔨 Building Docker image..."
                    // Build with both build number and latest tags
                    sh "docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest ."
                    echo "✅ Built: ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
                }
            }
        }

        stage('quality') {
            steps {
                script {
                    echo "🔍 Running quality checks with flake8..."
                    sh '''
                        . ${VENV_PATH}/bin/activate
                        
                        # Critical errors: fail the build
                        echo "   Checking critical errors (E9,F63,F7,F82)..."
                        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics \
                            --exclude=${VENV_PATH},.git,__pycache__,.pytest_cache
                        
                        # Style warnings: report but don't fail
                        echo "   Checking style guidelines..."
                        flake8 . --count --exit-zero \
                            --max-complexity=10 \
                            --max-line-length=127 \
                            --statistics \
                            --exclude=${VENV_PATH},.git,__pycache__,.pytest_cache
                    '''
                    echo "✅ Quality checks passed"
                }
            }
        }

        stage('test') {
            steps {
                script {
                    echo "🧪 Running tests with pytest..."
                    sh '''
                        . ${VENV_PATH}/bin/activate
                        
                        # Create reports directory
                        mkdir -p reports
                        
                        # Run pytest with coverage and JUnit XML output
                        # Supports both unittest and pytest style tests
                        pytest tests/ -v \
                            --cov=. \
                            --cov-report=xml:reports/coverage.xml \
                            --cov-report=html:reports/coverage-html \
                            --junitxml=reports/test-results.xml \
                            || exit $?
                    '''
                }
                post {
                    always {
                        // Publish test results and coverage
                        junit allowEmptyResults: true, testResults: 'reports/test-results.xml'
                        publishHTML(target: [
                            allowMissing: true,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: 'reports/coverage-html',
                            reportFiles: 'index.html',
                            reportName: 'Coverage Report'
                        ])
                    }
                }
            }
        }

        stage('deploy') {
            when {
                branch "${env.DEPLOY_BRANCH}"
            }
            steps {
                script {
                    echo "🚀 Deploying to ${DEPLOY_HOST}..."
                    
                    // Push Docker image to registry
                    withCredentials([usernamePassword(
                        credentialsId: REGISTRY_CREDS,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        echo "   Logging into Docker registry..."
                        sh "echo ${DOCKER_PASS} | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USER} --password-stdin"
                        
                        echo "   Pushing image: ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        
                        echo "   Pushing image: ${DOCKER_IMAGE}:latest"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest"
                        
                        sh "docker logout ${DOCKER_REGISTRY}"
                    }

                    // Deploy to laptop via SSH
                    echo "   Connecting via SSH to ${DEPLOY_HOST}..."
                    sshagent(credentials: [DEPLOY_SSH_CREDS]) {
                        sh """
                            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${DEPLOY_USER}@${DEPLOY_HOST} \\
                                "echo '${DOCKER_PASS}' | docker login ${DOCKER_REGISTRY} -u '${DOCKER_USER}' --password-stdin && \\
                                echo '   Pulling image...' && \\
                                docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} && \\
                                echo '   Stopping old container...' && \\
                                docker stop ${CONTAINER_NAME} 2>/dev/null || true && \\
                                echo '   Removing old container...' && \\
                                docker rm ${CONTAINER_NAME} 2>/dev/null || true && \\
                                echo '   Starting new container...' && \\
                                docker run -d --name ${CONTAINER_NAME} --restart=unless-stopped ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} && \\
                                echo '   Cleaning up old images...' && \\
                                docker image prune -f && \\
                                docker logout ${DOCKER_REGISTRY} && \\
                                echo '✅ Container ${CONTAINER_NAME} is running'"
                        """
                    }
                    echo "✅ Deployment complete: ${CONTAINER_NAME} on ${DEPLOY_HOST}"
                }
            }
        }
    }

    post {
        always {
            // Cleanup: remove local Docker images and workspace
            sh 'docker rmi ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} 2>/dev/null || true'
            sh 'docker rmi ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest 2>/dev/null || true'
            cleanWs()
        }
        failure {
            echo '❌ Pipeline FAILED - Check console output for details'
            // Optional: Send notification here (email/Slack)
        }
        success {
            echo "🎉 Pipeline SUCCESS"
            echo "   Image: ${DOCKER_IMAGE}:${BUILD_NUMBER}"
            echo "   Deployed to: ${DEPLOY_HOST}"
            echo "   Container: ${CONTAINER_NAME}"
        }
        unstable {
            echo '⚠️ Pipeline UNSTABLE - Tests or quality checks had issues'
        }
    }
}