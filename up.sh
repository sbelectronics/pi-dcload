pushd ../smb-pi-lib
rsync -avz --exclude "__history" --exclude "*~" --exclude "*.gif" --exclude "*.JPG" -e ssh . pi@198.0.0.25:/home/pi/smb-pi-lib
popd
rsync -avz --exclude "__history" --exclude "*~" --exclude "*.gif" --exclude "*.JPG" -e ssh . pi@198.0.0.25:/home/pi/dcload
