<?php

require_once __DIR__ . '/../Sources/visit-counter.php';

function counter_assert($condition, $message)
{
    if (!$condition) {
        fwrite(STDERR, "FAIL: $message\n");
        exit(1);
    }
}

if (isset($argv[1]) && $argv[1] === '--worker') {
    putenv('DOESTE_VISIT_COUNTER_DIR=' . $argv[2]);
    $_SERVER['HTTP_USER_AGENT'] = 'DOESTE counter concurrency test';
    $_SESSION = array();
    $value = doeste_visit_counter($argv[3]);
    exit($value === null ? 1 : 0);
}

$temporary = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'doeste-counter-' . uniqid('', true);
counter_assert(@mkdir($temporary, 0770, true), 'temporary directory');
putenv('DOESTE_VISIT_COUNTER_DIR=' . $temporary);
$_SERVER['HTTP_USER_AGENT'] = 'DOESTE counter test browser';

$_SESSION = array();
counter_assert(doeste_visit_counter('TED') === 1, 'first TED visit increments');
counter_assert(doeste_visit_counter('TED') === 1, 'refresh in same session does not increment');
$_SESSION = array();
counter_assert(doeste_visit_counter('TED') === 2, 'new TED session increments');
counter_assert(doeste_visit_counter('TEK') === 1, 'TEK total is independent');
counter_assert(doeste_visit_counter('TEJ') === 1, 'TEJ total is independent');

$beforeInternalPage = doeste_visit_counter_value('TED', false);
$internal = doeste_render_visit_counter('<p>Pesquisa</p>', 'cqp', 'TED');
counter_assert($internal === '<p>Pesquisa</p>', 'internal page remains unchanged');
counter_assert(doeste_visit_counter_value('TED', false) === $beforeInternalPage, 'internal page does not increment');

$_SESSION = array();
$_SERVER['HTTP_USER_AGENT'] = 'ExampleBot/1.0';
counter_assert(doeste_visit_counter('TED') === 2, 'simple bot does not increment');

file_put_contents($temporary . DIRECTORY_SEPARATOR . 'tek.count', "12483\n");
$rendered = doeste_render_visit_counter('<!-- DOESTE_VISIT_COUNTER -->', 'home', 'TEK');
counter_assert(strpos($rendered, 'Visitas: 12.483') !== false, 'Brazilian thousands separator');

$processes = array();
@unlink($temporary . DIRECTORY_SEPARATOR . 'ted.count');
for ($index = 0; $index < 12; $index++) {
    $processes[] = proc_open(array(PHP_BINARY, __FILE__, '--worker', $temporary, 'TED'), array(), $pipes);
}
foreach ($processes as $process) {
    counter_assert(is_resource($process) && proc_close($process) === 0, 'concurrent worker');
}
counter_assert(doeste_visit_counter_value('TED', false) === 12, 'concurrent increments are not lost');

$blocked = $temporary . DIRECTORY_SEPARATOR . 'not-a-directory';
file_put_contents($blocked, 'blocked');
putenv('DOESTE_VISIT_COUNTER_DIR=' . $blocked);
counter_assert(
    doeste_render_visit_counter('before<!-- DOESTE_VISIT_COUNTER -->after', 'home', 'TED') === 'beforeafter',
    'storage failure is silent'
);

foreach (glob($temporary . DIRECTORY_SEPARATOR . '*') as $file) @unlink($file);
@rmdir($temporary);
fwrite(STDOUT, "visit-counter=valid\n");

