import { notificationAPI } from './api';

function base64UrlToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function ensurePushSubscription(): Promise<void> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator) || !('PushManager' in window)) {
    return;
  }
  const publicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
  if (!publicKey) {
    return;
  }

  const permission: NotificationPermission = Notification.permission;
  if (permission === 'denied') {
    return;
  }

  const registration = await navigator.serviceWorker.register('/sw.js');
  let currentPermission: NotificationPermission = permission;
  if (currentPermission === 'default') {
    currentPermission = await Notification.requestPermission();
  }
  if (currentPermission !== 'granted') {
    return;
  }

  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: base64UrlToUint8Array(publicKey) as BufferSource,
    });
  }
  const json = subscription.toJSON();
  if (!json.endpoint || !json.keys?.p256dh || !json.keys?.auth) {
    return;
  }
  await notificationAPI.subscribePush({
    endpoint: json.endpoint,
    keys: {
      p256dh: json.keys.p256dh,
      auth: json.keys.auth,
    },
  });
}

export async function disablePushSubscription(): Promise<void> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }
  const registration = await navigator.serviceWorker.getRegistration();
  if (!registration || !('pushManager' in registration)) {
    return;
  }
  const subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    return;
  }
  const endpoint = subscription.endpoint;
  await subscription.unsubscribe();
  try {
    await notificationAPI.unsubscribePush(endpoint);
  } catch {
    // 解除時はサーバー側エラーでもブラウザ側解除を優先
  }
}

export async function getPushStatus(): Promise<{ permission: NotificationPermission; subscribed: boolean }> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator) || !('PushManager' in window)) {
    return { permission: 'denied', subscribed: false };
  }
  const permission: NotificationPermission = Notification.permission;
  const registration = await navigator.serviceWorker.getRegistration();
  const subscription = registration ? await registration.pushManager.getSubscription() : null;
  return { permission, subscribed: !!subscription };
}
