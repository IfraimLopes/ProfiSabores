import { Capacitor } from '@capacitor/core';
import { PushNotifications } from '@capacitor/push-notifications';
import { LocalNotifications } from '@capacitor/local-notifications';

window.CapacitorPlugins = {
    Capacitor,
    PushNotifications,
    LocalNotifications
};

console.log('PROFISABORES: plugins Capacitor carregados', {
    plataforma: Capacitor.getPlatform(),
    nativo: Capacitor.isNativePlatform()
});
