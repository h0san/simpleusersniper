# simpleusersniper
Simple user sniper for mobile termux/pydroid 3

How to use?

1. Install Termux from F-Droid (not Google Play).
2. Open Termux and type these commands one by one:

```
pkg update && pkg upgrade -y
pkg install python -y
pip install requests
termux-setup-storage
```

3. Copy the script code and save it as sniper.py in your phone's main storage (/sdcard/).
4. Open the file and change only this line:

```
TARGET = "https://example.com"
```

Replace example.com with your actual target site.

5. Choose what to scan by changing MODE:

· MODE = "all3" → scans all 3-letter combinations (17,576 usernames)
· MODE = "all2" → scans all 2-letter combinations (676 usernames)
· MODE = "wordlist" → reads usernames from wordlist.txt file
· MODE = "manual" → scans only usernames you write in MANUAL list

6. In Termux, navigate to storage and run:

```
cd /sdcard
python sniper.py
```

7. Speed settings:

· Fast WiFi: THREADS=150, DELAY=0.0
· Slow WiFi: THREADS=80, DELAY=0.05
· Mobile data: THREADS=40, DELAY=0.1
· If site blocks you: THREADS=15, DELAY=0.3

8. Results appear on screen as [AVAILABLE] and save to available.txt automatically.

If it only finds 11 and stops, the site is rate-limiting you. Lower THREADS to 20 and increase DELAY to 0.2, then run again.

I hope this has been helpful.
