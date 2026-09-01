<?php

// TEJ: representação em frases e exportação associada
// somente para usuários explicitamente autorizados.
$integral_access =
    $username &&
    in_array($user['permissions'], array('admin', 'integral'), true);

if (!$integral_access) {
    $maintext = showhtml("Pages/notli-integral.html");
    return;
}

include("$ttroot/common/Sources/block.php");
