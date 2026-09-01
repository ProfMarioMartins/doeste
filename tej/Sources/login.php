<?php

// TEJ: após autenticação, direciona o usuário para a pesquisa do corpus,
// em vez da área administrativa padrão do TEITOK.
$_GET['goon'] = '?action=cqp';

include("$ttroot/common/Sources/login.php");
