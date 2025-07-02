.RECIPEPREFIX = +
# -----------------------------------------------------------------------------------
#   WRW 17-Apr-2025 - Updated for Birdland-Qt

# -----------------------------------------------------------------------------------

all:
+   echo "Default action"

# -----------------------------------------------------------------------------------
#   Everything but the cruft. To reproduce development environment.

tar-dev:
+   cd ..;  tar --exclude ',*' \
+        --exclude '.e*' \
+        --exclude '__pycache__' \
+        --exclude Hold \
+        --exclude Prior \
+        -cvzf ~/Uploads/tar/birdland_qt-dev.tar.gz \
+        Birdland-Qt

# -------------------------------------------------------------------
#   Just what is needed to use birdland, most of above.

tar-user:
+   cd ..; tar --exclude ',*' \
+       --exclude '.e*' \
+       --exclude '__pycache__' \
+       --exclude '.ruff_cache' \
+       --exclude '.idea' \
+       --exclude 't' \
+       --exclude 'pysimplegui_qpalette_themes.csv' \
+       --exclude Development-Docs \
+       --exclude Exploratory \
+       --exclude Hold \
+       --exclude Prior \
+       -czvf ~/Uploads/tar/birdland_qt-user.tar.gz \
+       Birdland-Qt                           

# ------------------------------------------------------------

Distribution = ~/Uploads/Distribution
Files = birdland_qt* 
Dest = wrwetzel.com:www/Birdland-Qt/Downloads

upload:
+   rsync -av $(Distribution)/$(Files) $(Dest)

# ------------------------------------------------------------
