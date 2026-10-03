@echo off
rem Local PC2 video-only renderer compatibility; training arguments unchanged.
"C:\workspace\isaaclab_venv\Scripts\python.exe" -u "C:\dev\NConnect\tools\pc2_video_python_launcher.py" %*
exit /b %ERRORLEVEL%
