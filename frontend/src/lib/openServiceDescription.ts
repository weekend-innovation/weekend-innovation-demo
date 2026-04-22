export const OPEN_SERVICE_DESCRIPTION_EVENT = 'wi:open-service-description';

export function openServiceDescriptionModal(): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(OPEN_SERVICE_DESCRIPTION_EVENT));
}

