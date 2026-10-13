@echo off
cd /d "C:\boatrace"
git rm -r --cached . && git add . && git commit -m "fix" && git push
pause
