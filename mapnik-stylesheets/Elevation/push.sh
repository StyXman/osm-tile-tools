rsync --verbose --archive --update --progress --stats $@ \
    "./" "mustang.local::mdione/www/Elevation/"
