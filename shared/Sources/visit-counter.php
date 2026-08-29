<?php

/* Contador agregado: não registra IP, user-agent ou identificador persistente. */

function doeste_visit_counter_storage_dir()
{
    $configured = getenv('DOESTE_VISIT_COUNTER_DIR');
    if ($configured !== false && trim($configured) !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }
    return dirname(__DIR__) . DIRECTORY_SEPARATOR . 'var' . DIRECTORY_SEPARATOR . 'visit-counters';
}

function doeste_visit_counter_is_bot()
{
    $userAgent = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
    if ($userAgent === '') return true;
    return preg_match('/bot|crawler|spider|slurp|bingpreview|facebookexternalhit|headless|monitoring/i', $userAgent) === 1;
}

function doeste_visit_counter_file($corpus)
{
    $corpus = strtolower((string) $corpus);
    if (!in_array($corpus, array('ted', 'tej', 'tek'), true)) return null;
    $directory = doeste_visit_counter_storage_dir();
    if (!is_dir($directory) && !@mkdir($directory, 0770, true) && !is_dir($directory)) return null;
    return $directory . DIRECTORY_SEPARATOR . $corpus . '.count';
}

function doeste_visit_counter_value($corpus, $increment)
{
    $path = doeste_visit_counter_file($corpus);
    if ($path === null) return null;
    $handle = @fopen($path, 'c+');
    if ($handle === false) return null;
    if (!@flock($handle, LOCK_EX)) {
        @fclose($handle);
        return null;
    }

    @rewind($handle);
    $raw = stream_get_contents($handle);
    $count = preg_match('/^\s*\d+\s*$/', (string) $raw) ? (int) trim($raw) : 0;
    if ($increment) {
        $count++;
        $serialized = (string) $count . "\n";
        @rewind($handle);
        $truncated = @ftruncate($handle, 0);
        $written = $truncated ? @fwrite($handle, $serialized) : false;
        if (!$truncated || $written !== strlen($serialized) || !@fflush($handle)) {
            @flock($handle, LOCK_UN);
            @fclose($handle);
            return null;
        }
    }

    @flock($handle, LOCK_UN);
    @fclose($handle);
    return $count;
}

function doeste_visit_counter($corpus)
{
    if (session_status() !== PHP_SESSION_ACTIVE) @session_start();
    $sessionKey = 'doeste_visit_counted_' . strtolower((string) $corpus);
    $alreadyCounted = isset($_SESSION[$sessionKey]);
    $increment = !$alreadyCounted && !doeste_visit_counter_is_bot();
    $count = doeste_visit_counter_value($corpus, $increment);
    if ($increment && $count !== null) $_SESSION[$sessionKey] = true;
    return $count;
}

function doeste_render_visit_counter($maintext, $action, $corpus)
{
    $marker = '<!-- DOESTE_VISIT_COUNTER -->';
    if (strpos($maintext, $marker) === false) return $maintext;
    if ($action !== 'home') return str_replace($marker, '', $maintext);
    $count = doeste_visit_counter($corpus);
    if ($count === null) return str_replace($marker, '', $maintext);
    $formatted = number_format($count, 0, ',', '.');
    return str_replace($marker, '<p class="corpus-visit-counter">Visitas: ' . $formatted . '</p>', $maintext);
}

