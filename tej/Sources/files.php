<?php

// TEJ: a administração e enumeração dos arquivos do corpus
// são restritas exclusivamente a administradores.
$admin_access =
    $username &&
    $user['permissions'] === 'admin';

if (!$admin_access) {
    $maintext = showhtml("Pages/notli.html");
    return;
}

include("$ttroot/common/Sources/files.php");
