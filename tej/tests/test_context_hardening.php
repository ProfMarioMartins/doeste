<?php

require_once __DIR__ . '/../Sources/context-policy.php';

function assert_same($expected, $actual, string $message): void
{
    if ($expected !== $actual) {
        fwrite(STDERR, "FAIL: $message\nExpected: " . var_export($expected, true)
            . "\nActual: " . var_export($actual, true) . "\n");
        exit(1);
    }
}

function cqp_policy(array $get = array(), array $post = array(), array $user = array()): array
{
    tej_apply_public_cqp_policy($get, $post, $user);
    return array($get, $post);
}

function context_policy(array $get = array(), array $user = array()): array
{
    tej_apply_public_context_policy($get, $user);
    return $get;
}

// CQP/KWIC público: todas as opções normais da interface são preservadas.
foreach (array(3, 4, 5, 6, 7) as $size) {
    [, $post] = cqp_policy(array(), array('style' => 'kwic', 'context' => (string) $size));
    assert_same($size, $post['context'], "KWIC $size deve permanecer disponível");
}

[, $post] = cqp_policy(array(), array('style' => 'kwic', 'context' => '999'));
assert_same(7, $post['context'], 'KWIC acima do teto deve ser limitado a 7');

foreach (array(5, 15, 30, 50, 100) as $size) {
    [, $post] = cqp_policy(array(), array('style' => 'context', 'substyle' => 'tok', 'tokcnt' => (string) $size));
    assert_same($size, $post['tokcnt'], "Contexto de $size tokens deve permanecer disponível");
}

[, $post] = cqp_policy(array(), array('style' => 'context', 'substyle' => 'tok', 'tokcnt' => '100000'));
assert_same(100, $post['tokcnt'], 'Contexto por tokens acima do teto deve ser limitado a 100');

[, $post] = cqp_policy(array(), array('style' => 'context', 'substyle' => 's'));
assert_same('s', $post['substyle'], 'Contexto sentencial deve permanecer disponível');

[, $post] = cqp_policy(array(), array('style' => 'context', 'substyle' => 'text', 'tokcnt' => '30'));
assert_same('tok', $post['substyle'], 'Unidade estrutural não autorizada deve virar contexto por tokens');

[, $post] = cqp_policy(array(), array('style' => 'invalid', 'context' => '999', 'max' => '50000'));
assert_same('kwic', $post['style'], 'Estilo desconhecido deve virar KWIC');
assert_same(7, $post['context'], 'Contexto GET/POST manual deve ser limitado');
assert_same('50000', $post['max'], 'A paginação normal do TEITOK não pertence à política de contexto');

// action=context público: pos é a única âncora posicional confiável.
$get = context_policy(array(
    'pos' => '500',
    'context' => '100',
    'leftpos' => '1',
    'rightpos' => '999999',
));
assert_same(100, $get['context'], 'Contexto numérico 100 deve permanecer disponível');
assert_same(500, $get['leftpos'], 'leftpos forjado deve ser substituído por pos');
assert_same(500, $get['rightpos'], 'rightpos forjado deve ser substituído por pos');

$get = context_policy(array('pos' => '500', 'context' => '9999'));
assert_same(100, $get['context'], 'Contexto numérico excessivo deve ser limitado a 100');
assert_same(500, $get['leftpos'], 'pos deve definir a âncora esquerda');
assert_same(500, $get['rightpos'], 'pos deve definir a âncora direita');

$get = context_policy(array('pos' => '500', 'context' => 's'));
assert_same('s', $get['context'], 'Sentença deve ser aceita como estrutura pública');
assert_same(500, $get['leftpos'], 'Contexto sentencial deve usar pos como âncora');
assert_same(500, $get['rightpos'], 'Contexto sentencial deve usar uma única âncora');

$get = context_policy(array('tid' => 'w-25', 'context' => '30', 'leftpos' => '1', 'rightpos' => '999999'));
assert_same('w-25', $get['tid'], 'tid utilizável deve ser preservado');
assert_same(false, isset($get['leftpos']), 'leftpos deve ser removido quando o runtime resolver tid');
assert_same(false, isset($get['rightpos']), 'rightpos deve ser removido quando o runtime resolver tid');

$get = context_policy(array('context' => '30', 'leftpos' => '1', 'rightpos' => '999999'));
assert_same(false, isset($get['leftpos']), 'leftpos isolado não pode recuperar texto');
assert_same(false, isset($get['rightpos']), 'rightpos isolado não pode recuperar texto');
assert_same(false, isset($get['pos']), 'requisição sem âncora deve permanecer sem pos');
assert_same(false, isset($get['tid']), 'requisição sem âncora deve permanecer sem tid');

// HTML, raw e JSON recebem exatamente a mesma normalização posicional.
foreach (array('html', 'raw', 'json') as $format) {
    $get = context_policy(array(
        'format' => $format,
        'pos' => '700',
        'context' => '9999',
        'leftpos' => '1',
        'rightpos' => '100000',
    ));
    assert_same(100, $get['context'], "Contexto $format deve respeitar o mesmo teto");
    assert_same(700, $get['leftpos'], "leftpos $format deve ser normalizado para pos");
    assert_same(700, $get['rightpos'], "rightpos $format deve ser normalizado para pos");
}

$get = context_policy(array('type' => 'xpath', 'context' => 'text', 'pos' => '20'));
assert_same(false, isset($get['type']), 'Modo XPath público deve ser removido');
assert_same('s', $get['context'], 'XPath público deve cair no contexto sentencial permitido');

$get = context_policy(array('type' => 'sent', 'context' => 's', 'tid' => 'w-1'));
assert_same('sent', $get['type'], 'Modo sentencial nativo deve permanecer disponível com tid');

$get = context_policy(array('type' => 'sent', 'context' => 's', 'leftpos' => '10'));
assert_same(false, isset($get['type']), 'Modo sentencial sem tid não pode contornar a falha segura');

// Acesso integral: nenhum parâmetro deve ser reescrito.
foreach (array('admin', 'integral') as $permission) {
    $original_get = array('style' => 'other', 'context' => '9999', 'leftpos' => '1', 'rightpos' => '999999', 'type' => 'xpath');
    $original_post = array('style' => 'context', 'substyle' => 'text', 'tokcnt' => '9999', 'max' => '50000');
    [$get, $post] = cqp_policy($original_get, $original_post, array('permissions' => $permission));
    assert_same($original_get, $get, "$permission deve manter GET integral no CQP");
    assert_same($original_post, $post, "$permission deve manter POST integral no CQP");
    assert_same($original_get, context_policy($original_get, array('permissions' => $permission)), "$permission deve manter contexto integral");
}

print "OK: política pública de contexto do TEJ validada\n";
