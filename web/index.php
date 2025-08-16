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
$action = $_POST['action'] ?? null;
if (strtolower($action) == 'nav') {
    /* Navigating */
    $page = $_POST['page'] ?? "1";
    $entries = $_POST['entries'] ?? "60";
    $data = [];
    if ($page == "0") { die(json_encode(["error" => "bad page 0"])); }
    $query = "SELECT `pk`, `hash` FROM `entries` ORDER BY `pk` ASC LIMIT " . (($page - 1) * $entries) . "," . $entries;
    $res = mysqli_query($link, $query);
    while ($r = mysqli_fetch_assoc($res)) {
        $data[] = $r['pk'] . ':' . $r['hash'];
    }
    echo json_encode(['data' => $data]);
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
        <style>
        </style>
        <script>
var thumbnail_width = 160;
var current_page = 1;
window.addEventListener('load', (e) => {
    loadPage(current_page);
    document.onkeydown = function (e) {
        e = e || window.event;
        if (e.keyCode == 37) { // left arrow key
            if (current_page > 1) {
                loadPage(current_page - 1);
            }
        }
        if (e.keyCode == 39) { // right arrow key
            loadPage(current_page + 1);
        }
    };
});
function loadPage(page) {
  current_page = page;
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
      let res = xhr.responseText;
      let j = JSON.parse(res);
      let pagediv = document.getElementById('page'); pagediv.innerHTML = '';
      let navdiv = document.getElementById('nav'); navdiv.innerHTML = '';
      if ("data" in j) {
        page_data = ''
        items = j.data;
        row_length = 6;
        for (let i = 0; i < items.length; i++) {
            item = j.data[i];
            entries = item.split(':');
            primary_key = entries[0];
            hash = entries[1];
            thumbnail = hash.substr(0, 7);
            if (row_length == 6) {
                page_data = page_data + '<div class="row">';
            }
            page_data = page_data + '<div class="col">' + '<img src="archive-thumbnails/' + thumbnail + '.jpg" width="' + thumbnail_width + '" /></div>';
            row_length--;
            if (row_length == 0) {
                page_data = page_data + '</div>';
                row_length = 6;
            }
        }
        pagediv.innerHTML = page_data;
        /* Navigation */
        let nav_data = '';
        if (page > 1) {
            nav_data = '<a href="javascript:loadPage(' + (page - 1) + ');">&lt; Previous</a> | ';
        } else {
            nav_data = '&lt; Previous | ';
        }
        nav_data = nav_data + 'Page ' + page + ' | <a href="javascript:loadPage(' + (page + 1) + ');">Next &gt;</a>'
        nav.innerHTML = nav_data;
      }
    }
  };
  xhr.open('POST', 'index.php', true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.send('action=nav&page=' + page);
}
        </script>
    </head>
    <body>
        <div class="container">
            <!-- header -->
            <div class="row">
                <div class="col text-center">
                    <h1>digital-archive</h1>
                </div>
            </div>
            <!-- search -->
            <div class="row">
                <div class="col text-center">
                    <input type="text" value="" placeholder="" />
                </div>
            </div>
            <!-- navigation -->
            <div class="row">
                <div id="nav" class="col text-center"></div>
            </div>
            <!-- page -->
            <div class="row"><div class="col"><hr /></div></div>
            <div id="page"></div>
            <div class="row"><div class="col"><hr /></div></div>
            <!-- footer -->
            <div class="row">
                <div class="col text-center">
                    <small>&copy;2025 Aug 16 | Matthew James Heick</small>
                </div>
            </div>
        </div>
        <script src="bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
    </body>
</html>
