<?php
/* housekeeping */

/* Does our symlink for where the thumbnails are stored exist? */
if (!file_exists('archive-thumbnails')) { die('archive-thumbnails do not exist. create a symlink here to where they are so we can make prettiness show up'); }

/* Our database connection information */
$MYSQL = [
    'hostname' => 'localhost',
    'username' => 'digital_archive',
    'password' => 'digital_archive',
    'database' => 'digital_archive',
];
$link = mysqli_connect($MYSQL['hostname'], $MYSQL['username'], $MYSQL['password'], $MYSQL['database']);
if (!$link) { die('cannot connect to database. reconfigure, then try again.'); }

/**
 * Our inbound $_POST requests are here
 * action = nav > Navigation-related
 * action = edit > Viewing/editing data
 * All these will be json responses. Badness is in {'error' => ''}
 */
$action = $_POST['action'] ?? 'unknown';
if ($action == 'unknown') { die(json_encode(['error' => 'bad parameter passed in for action'])); }
if (strtolower($action) == 'nav') {
    /* Navigating */
    die();
}
if (strtolower($action) == 'edit') {
    /* Editing metadata */
    die();
}


?><!doctype html>
<html lang="en">
    <head>
        <title>digital-archiver</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
        <script>
var page = 1;
window.addEventListener('load', (e) => {
    loadPage(page);
});
function loadPage(page) {

}
        </script>
    </head>
    <body>
        <div class="container">
            <div id="page_top"></div>
            <div id="page_search"></div>
            <div id="page_navigation_top"></div>
            <div id="page"></div>
            <div id="page_navigation_bottom"></div>
            <div id="page_bottom"></div>
        </div>
        <script src="bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
    </body>
</html>