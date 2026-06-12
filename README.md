# MediaPipe-Photo-Booth

In this app the goal is to use a webcam and MediaPipe library to be able to detect hand gestures and emotions. By using specific gestures, user is able to take a picture.

Functionalities:
1. Smile detection
2. Emojis generating after detecting a smile
3. Detecting hand gestures: thumbs-up and peace sign
4. Taking a picture after detecting one of the hand gestures
5. Generating QR code for downloading the picture

How to run:
1. Clone or download from the https://github.com/lkocis/MediaPipe-Photo-Booth.git repository
2. Open terminal from the directory where the project is set
3. Run "docker compose up --build"
4. After it had loaded, in the browser open localhost:5000
5. To shut down, run "docker compose down"