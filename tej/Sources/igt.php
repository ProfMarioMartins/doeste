<?php

// TEJ: a visualização interlinear expõe o conteúdo integral
// e, por isso, é restrita a usuários explicitamente autorizados.
$integral_access =
    $username &&
    in_array($user['permissions'], array('admin', 'integral'), true);

if (!$integral_access) {
    $maintext = showhtml("Pages/notli-integral.html");
    return;
}

include("$ttroot/common/Sources/igt.php");
