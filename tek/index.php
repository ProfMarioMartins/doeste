<?php

// TEITOK is an external runtime and is not incorporated into this repository.
$ttroot = getenv('TT_ROOT');
if (!$ttroot) {
    if (is_dir('/home/git/TEITOK')) $ttroot = '/home/git/TEITOK';
    else $ttroot = '..';
}

date_default_timezone_set('UTC');
ini_set('display_errors', '0');
error_reporting(E_ERROR | E_WARNING);

include("$ttroot/common/Sources/main.php");

?>
