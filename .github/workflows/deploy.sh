name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Sync repo to server
        uses: easingthemes/ssh-deploy@v5.0.3
        with:
          REMOTE_HOST: ${{ secrets.SSH_HOST }}
          REMOTE_USER: ${{ secrets.SSH_USER }}
          SSH_PRIVATE_KEY: ${{ secrets.SSH_KEY }}
          SOURCE: "./"
          TARGET: "${{ secrets.APP_DIR }}/repo"
          EXCLUDE: |
            .git*
            .github/

      - name: Install deps & restart (run deploy.sh)
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            export APP_DIR="${{ secrets.APP_DIR }}"
            export REPO_DIR="${{ secrets.APP_DIR }}/repo"
            export VENV="${{ secrets.APP_DIR }}/venv"
            export SERVICE="shipy.service"
            cd "$REPO_DIR"
            bash ./deploy.sh
