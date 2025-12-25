"use client";

/**
 * Страница настроек профиля.
 *
 * Отображает информацию о пользователе из Telegram.
 * Данные readonly — изменить можно только через Telegram.
 */

import { useAuth } from "@/contexts/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Settings,
  User,
  Mail,
  Calendar,
  Shield,
  LogOut,
  Loader2,
} from "lucide-react";

export default function SettingsPage() {
  const { user, loading, logout } = useAuth();

  // Загрузка
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-warm-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Если нет пользователя
  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-warm-gray-600">Пользователь не найден</p>
      </div>
    );
  }

  /**
   * Форматирование даты регистрации.
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  /**
   * Получение инициалов для аватара.
   */
  const getInitials = () => {
    const first = user.first_name?.[0] || "";
    const last = user.last_name?.[0] || "";
    return (first + last).toUpperCase() || "U";
  };

  return (
    <div className="space-y-8">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
          Настройки
        </h1>
        <p className="text-warm-gray-600">Управление вашим профилем</p>
      </div>

      {/* Профиль пользователя */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5 text-emerald-600" />
            Профиль
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-6">
            {/* Аватар */}
            <Avatar className="w-20 h-20">
              {user.photo_url ? (
                <AvatarImage
                  src={user.photo_url}
                  alt={`${user.first_name} ${user.last_name || ""}`}
                />
              ) : (
                <AvatarFallback className="text-2xl bg-emerald-100 text-emerald-700">
                  {getInitials()}
                </AvatarFallback>
              )}
            </Avatar>

            {/* Информация */}
            <div className="flex-1 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Имя */}
                <div>
                  <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                    Имя
                  </label>
                  <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                    <p className="text-warm-gray-900">
                      {user.first_name} {user.last_name || ""}
                    </p>
                  </div>
                </div>

                {/* Username */}
                <div>
                  <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                    Username
                  </label>
                  <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                    <p className="text-warm-gray-900">
                      {user.username ? `@${user.username}` : "—"}
                    </p>
                  </div>
                </div>

                {/* Telegram ID */}
                <div>
                  <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                    <Shield className="w-4 h-4 inline mr-1" />
                    Telegram ID
                  </label>
                  <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                    <p className="text-warm-gray-900 font-mono text-sm">
                      {user.telegram_id}
                    </p>
                  </div>
                </div>

                {/* Дата регистрации */}
                <div>
                  <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    Зарегистрирован
                  </label>
                  <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                    <p className="text-warm-gray-900">
                      {formatDate(user.created_at)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Информация о readonly */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>Информация:</strong> Данные профиля получены из
                  Telegram и не могут быть изменены напрямую. Для изменения
                  обновите ваш профиль в Telegram.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Уведомления (заглушка) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-emerald-600" />
            Уведомления
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-warm-gray-300 rounded-lg p-8">
            <div className="text-center">
              <Mail className="w-12 h-12 text-warm-gray-400 mx-auto mb-4" />
              <p className="text-warm-gray-600">
                Настройки уведомлений будут добавлены в следующем обновлении
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Дополнительные настройки */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-emerald-600" />
            Дополнительно
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-warm-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-warm-gray-900">Язык интерфейса</p>
                <p className="text-sm text-warm-gray-600">
                  Выберите язык приложения
                </p>
              </div>
              <div className="px-4 py-2 bg-white border border-warm-gray-200 rounded-lg">
                <span className="text-warm-gray-900">Русский</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-warm-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-warm-gray-900">Формат даты</p>
                <p className="text-sm text-warm-gray-600">
                  Формат отображения даты и времени
                </p>
              </div>
              <div className="px-4 py-2 bg-white border border-warm-gray-200 rounded-lg">
                <span className="text-warm-gray-900">ДД.ММ.ГГГГ</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Выход из аккаунта */}
      <Card className="border-red-200">
        <CardContent className="py-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-warm-gray-900">Выйти из аккаунта</p>
              <p className="text-sm text-warm-gray-600">
                Вы будете перенаправлены на страницу входа
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={logout}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="w-5 h-5" />
              Выйти
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
