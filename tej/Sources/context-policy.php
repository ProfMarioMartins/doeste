<?php

/**
 * Limites públicos de contexto do Corpus TEJ.
 *
 * Este arquivo é carregado pelos overrides locais de CQP e contexto antes do
 * runtime compartilhado. Usuários com permissão "admin" ou "integral" não
 * têm suas requisições alteradas.
 */

const TEJ_PUBLIC_KWIC_MIN = 3;
const TEJ_PUBLIC_KWIC_MAX = 7;
const TEJ_PUBLIC_TOKEN_CONTEXT_MIN = 5;
const TEJ_PUBLIC_TOKEN_CONTEXT_MAX = 100;

function tej_has_integral_access($user): bool
{
    if (!is_array($user)) {
        return false;
    }

    $permission = isset($user['permissions']) ? (string) $user['permissions'] : '';
    return $permission === 'admin' || $permission === 'integral';
}

function tej_scalar_request_value(array $primary, array $secondary, string $key, $default = null)
{
    if (array_key_exists($key, $primary) && is_scalar($primary[$key])) {
        return $primary[$key];
    }
    if (array_key_exists($key, $secondary) && is_scalar($secondary[$key])) {
        return $secondary[$key];
    }
    return $default;
}

function tej_bounded_integer($value, int $default, int $minimum, int $maximum): int
{
    if (is_int($value)) {
        $integer = $value;
    } elseif (is_string($value) && preg_match('/^\d+$/D', $value)) {
        $integer = (int) $value;
    } else {
        $integer = $default;
    }

    return max($minimum, min($maximum, $integer));
}

function tej_apply_public_cqp_policy(array &$get, array &$post, $user): void
{
    if (tej_has_integral_access($user)) {
        return;
    }

    $style = strtolower((string) tej_scalar_request_value($post, $get, 'style', 'kwic'));
    if ($style !== 'context') {
        $style = 'kwic';
    }
    $post['style'] = $style;
    $get['style'] = $style;

    if ($style === 'kwic') {
        $context = tej_bounded_integer(
            tej_scalar_request_value($post, $get, 'context', 5),
            5,
            TEJ_PUBLIC_KWIC_MIN,
            TEJ_PUBLIC_KWIC_MAX
        );
        $post['context'] = $context;
        $get['context'] = $context;
    } else {
        $substyle = strtolower((string) tej_scalar_request_value($post, $get, 'substyle', 'tok'));
        if ($substyle !== 's') {
            $substyle = 'tok';
        }
        $post['substyle'] = $substyle;
        $get['substyle'] = $substyle;

        if ($substyle === 'tok') {
            $tokcnt = tej_bounded_integer(
                tej_scalar_request_value($post, $get, 'tokcnt', 30),
                30,
                TEJ_PUBLIC_TOKEN_CONTEXT_MIN,
                TEJ_PUBLIC_TOKEN_CONTEXT_MAX
            );
            $post['tokcnt'] = $tokcnt;
            $get['tokcnt'] = $tokcnt;
        }
    }
}

function tej_nonnegative_position($value): ?int
{
    if (is_int($value) && $value >= 0) {
        return $value;
    }
    if (is_string($value) && preg_match('/^\d+$/D', $value)) {
        return (int) $value;
    }
    return null;
}

function tej_usable_token_id($value): ?string
{
    if (!is_string($value) || !preg_match('/^[A-Za-z0-9_.:-]+$/D', $value)) {
        return null;
    }
    return $value;
}

function tej_apply_public_context_policy(array &$get, $user): void
{
    if (tej_has_integral_access($user)) {
        return;
    }

    $requested_context = tej_scalar_request_value($get, array(), 'context', 's');
    if (is_int($requested_context) || (is_string($requested_context) && preg_match('/^\d+$/D', $requested_context))) {
        $context = tej_bounded_integer(
            $requested_context,
            TEJ_PUBLIC_TOKEN_CONTEXT_MAX,
            0,
            TEJ_PUBLIC_TOKEN_CONTEXT_MAX
        );
    } else {
        // "s" é a única unidade estrutural pública configurada no TEJ.
        $context = 's';
    }
    $get['context'] = $context;

    $pos = tej_nonnegative_position(tej_scalar_request_value($get, array(), 'pos'));
    $tid = tej_usable_token_id(tej_scalar_request_value($get, array(), 'tid'));

    if ($tid !== null) {
        $get['tid'] = $tid;
    } else {
        unset($get['tid']);
    }

    // O modo XPath permite selecionar estruturas fora da política pública.
    // O modo sentencial nativo permanece autorizado quando há token-âncora.
    $type = strtolower((string) tej_scalar_request_value($get, array(), 'type', ''));
    if ($type === 'sent' && $tid !== null) {
        $get['type'] = 'sent';
    } else {
        unset($get['type']);
    }

    if ($pos !== null) {
        // leftpos/rightpos do cliente nunca ampliam a âncora pública.
        $get['pos'] = $pos;
        $get['leftpos'] = $pos;
        $get['rightpos'] = $pos;
    } else {
        // Com tid, o runtime resolve a posição CQP. Sem tid, a ausência destas
        // posições aciona sua falha segura sem recuperar conteúdo textual.
        unset($get['pos']);
        unset($get['leftpos'], $get['rightpos']);
    }
}
