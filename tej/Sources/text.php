<?php

// TEJ: acesso ao texto integral somente para usuários explicitamente autorizados.
// Administradores mantêm acesso; pesquisadores autorizados usam a permissão "integral".

$integral_access =
    $username &&
    in_array($user['permissions'], array('admin', 'integral'), true);

if (!$integral_access) {
    $maintext = showhtml("Pages/notli-integral.html");
    return;
}

include("$ttroot/common/Sources/text.php");
