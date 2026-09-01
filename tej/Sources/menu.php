<?php

// TEJ: utiliza o menu padrão do TEITOK.
include("$ttroot/common/Sources/menu.php");

// TEJ: substitui a identificação técnica do usuário por ações claras de sessão.
if ($username) {
    $menu = preg_replace(
        '~<hr>(?:<span[^>]*>)?g?user(?:</span>)?:\s*<a[^>]*href=[\'"]index\.php\?action=user[\'"][^>]*>.*?</a><hr>~is',
        '<hr><ul style="text-align: left"><li><a href="index.php?action=user">Meu perfil</a></li><li><a href="index.php?action=login&amp;act=exit">Sair</a></li></ul><hr>',
        $menu
    );
}

// Pesquisadores com acesso integral não possuem funções administrativas.
if ($username && $user['permissions'] === 'integral') {
    $menu = preg_replace(
        '~<ul[^>]*><li[^>]*><a[^>]*href=[\'"][^\'"]*action=(?:admin|classify|files)[^\'"]*[\'"][^>]*>.*?</a></ul>~is',
        '',
        $menu
    );
}

// O perfil integral é somente-leitura: oculta controles de edição
// que o TEITOK exibe genericamente para qualquer usuário autenticado.
if ($username && $user['permissions'] === 'integral') {
    $menu .= '<style>.adminpart { display: none !important; }</style>';
}
