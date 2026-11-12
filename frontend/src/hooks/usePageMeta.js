// File Name: usePageMeta.js
// Description: Lightweight document-head hook (no react-helmet dependency). Sets
// document.title, meta description/robots, Open Graph + Twitter tags and the canonical
// link for the current route, then restores the previous head state on unmount so a
// public page never leaks its meta into a private screen (and vice versa).
// Created At: 2026-11-13
// Created By: AI Agent

import { useEffect } from 'react';

// Placeholder production domain — keep in sync with public/robots.txt & public/sitemap.xml.
export const SITE_URL = (import.meta.env.VITE_PUBLIC_SITE_URL || 'https://smartlms.example.com').replace(/\/+$/, '');
export const SITE_NAME = 'SmartLMS';

/**
 * Create/update a <meta> tag and return a cleanup that restores the previous value
 * (or removes the tag entirely when this hook created it).
 */
function upsertMeta(attribute, key, content) {
  if (content === undefined || content === null || content === '') return () => {};

  const selector = `meta[${attribute}="${key}"]`;
  let element = document.head.querySelector(selector);
  const existed = Boolean(element);
  const previousContent = existed ? element.getAttribute('content') : null;

  if (!element) {
    element = document.createElement('meta');
    element.setAttribute(attribute, key);
    document.head.appendChild(element);
  }
  element.setAttribute('content', content);

  return () => {
    if (!existed) {
      element.remove();
      return;
    }
    if (previousContent === null) element.removeAttribute('content');
    else element.setAttribute('content', previousContent);
  };
}

/** Create/update <link rel="canonical"> and return a cleanup restoring the old href. */
function upsertCanonical(href) {
  if (!href) return () => {};

  let element = document.head.querySelector('link[rel="canonical"]');
  const existed = Boolean(element);
  const previousHref = existed ? element.getAttribute('href') : null;

  if (!element) {
    element = document.createElement('link');
    element.setAttribute('rel', 'canonical');
    document.head.appendChild(element);
  }
  element.setAttribute('href', href);

  return () => {
    if (!existed) {
      element.remove();
      return;
    }
    if (previousHref === null) element.removeAttribute('href');
    else element.setAttribute('href', previousHref);
  };
}

/**
 * @param {Object} meta
 * @param {string} [meta.title] Document title (also reused for og:title / twitter:title).
 * @param {string} [meta.description] Meta description (also reused for OG/Twitter).
 * @param {string} [meta.canonicalPath] Route path, e.g. "/login" — resolved against SITE_URL.
 * @param {string} [meta.robots] Robots directive, e.g. "index,follow" / "noindex,nofollow".
 * @param {string} [meta.ogTitle]
 * @param {string} [meta.ogDescription]
 * @param {string} [meta.ogType] Defaults to "website".
 * @param {string} [meta.ogImage]
 */
export default function usePageMeta({
  title,
  description,
  canonicalPath,
  robots,
  ogTitle,
  ogDescription,
  ogType = 'website',
  ogImage,
} = {}) {
  useEffect(() => {
    const cleanups = [];
    const previousTitle = document.title;

    if (title) document.title = title;

    if (description) cleanups.push(upsertMeta('name', 'description', description));
    if (robots) cleanups.push(upsertMeta('name', 'robots', robots));

    // Open Graph
    if (title || ogTitle) cleanups.push(upsertMeta('property', 'og:title', ogTitle || title));
    if (description || ogDescription) {
      cleanups.push(upsertMeta('property', 'og:description', ogDescription || description));
    }
    if (ogType) cleanups.push(upsertMeta('property', 'og:type', ogType));
    cleanups.push(upsertMeta('property', 'og:site_name', SITE_NAME));
    cleanups.push(upsertMeta('property', 'og:locale', 'vi_VN'));
    if (ogImage) cleanups.push(upsertMeta('property', 'og:image', ogImage));

    // Twitter card
    if (title || ogTitle) cleanups.push(upsertMeta('name', 'twitter:title', ogTitle || title));
    if (description || ogDescription) {
      cleanups.push(upsertMeta('name', 'twitter:description', ogDescription || description));
    }
    cleanups.push(upsertMeta('name', 'twitter:card', ogImage ? 'summary_large_image' : 'summary'));

    if (canonicalPath) {
      const path = canonicalPath.startsWith('/') ? canonicalPath : `/${canonicalPath}`;
      cleanups.push(upsertCanonical(`${SITE_URL}${path}`));
    }

    return () => {
      document.title = previousTitle;
      cleanups.forEach((restore) => restore());
    };
  }, [title, description, canonicalPath, robots, ogTitle, ogDescription, ogType, ogImage]);
}
