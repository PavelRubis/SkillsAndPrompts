#!/usr/bin/env node
// CLI-обёртка над плагином @sharleysoft/openclaw-yandex-maps-places-review.
// Запуск: node fetch-reviews.mjs <url Яндекс.Карт> [count]
// Печатает JSON { sourceUrl, requestedCount, fetchedAt, reviews: [{date,text,url}], stats } в stdout.
// Логи pino идут в stderr, поэтому stdout остаётся чистым JSON.

import { createToolCallHandlers } from '@sharleysoft/openclaw-yandex-maps-places-review/dist/Composition/create-tool-call-handlers.js';

const url = process.argv[2] ?? process.env.YANDEX_MAPS_PLACE_URL;
const rawCount = process.argv[3] ?? process.env.YANDEX_MAPS_REVIEW_COUNT ?? '100';
const count = Number(rawCount);
const logLevel = process.env.LOG_LEVEL ?? 'silent';

if (!url) {
    console.error('Usage: node fetch-reviews.mjs <YANDEX_MAPS_PLACE_URL> [count]');
    process.exit(1);
}
if (!Number.isInteger(count) || count < 1 || count > 500) {
    console.error('count must be an integer from 1 to 500.');
    process.exit(1);
}

const handlers = createToolCallHandlers({ logLevel });
const result = await handlers.getYandexMapsPlaceReviews.handle({
    url,
    count,
    headed: process.env.HEADED === '1'
});

process.stdout.write(JSON.stringify(result) + '\n');
