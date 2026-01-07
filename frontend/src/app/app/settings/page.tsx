"use client";

/**
 * Страница настроек профиля.
 *
 * Отображает информацию о пользователе из Telegram.
 * Данные readonly — изменить можно только через Telegram.
 * Enterprise пользователи могут управлять API ключами.
 */

import { useState, useEffect, useCallback } from "react";
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
  Key,
  Copy,
  Check,
  Trash2,
  AlertTriangle,
  Tag,
  Save,
} from "lucide-react";
import type { ApiKeyInfo, ApiKeyCreatedResponse, LabelFormat } from "@/types/api";
import {
  getUserPreferences,
  updateUserPreferences,
  type LabelLayout,
  type LabelSize,
} from "@/lib/api";

export default function SettingsPage() {
  const { user, loading, logout } = useAuth();

  // Состояние для API ключей (только Enterprise)
  const [apiKeyInfo, setApiKeyInfo] = useState<ApiKeyInfo | null>(null);
  const [apiKeyLoading, setApiKeyLoading] = useState(false);
  const [apiKeyError, setApiKeyError] = useState<string | null>(null);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Состояние для настроек этикеток
  const [labelPrefsLoading, setLabelPrefsLoading] = useState(false);
  const [labelPrefsSaving, setLabelPrefsSaving] = useState(false);
  const [labelPrefsError, setLabelPrefsError] = useState<string | null>(null);
  const [labelPrefsSaved, setLabelPrefsSaved] = useState(false);

  // Временные значения для редактирования
  const [orgName, setOrgName] = useState("");
  const [inn, setInn] = useState("");
  const [layout, setLayout] = useState<LabelLayout>("basic");
  const [labelSize, setLabelSize] = useState<LabelSize>("58x40");
  const [labelFormat, setLabelFormat] = useState<LabelFormat>("combined");
  const [showArticle, setShowArticle] = useState(true);
  const [showSizeColor, setShowSizeColor] = useState(true);
  const [showName, setShowName] = useState(true);
  const [customLines, setCustomLines] = useState<string[]>(["", "", ""]);

  /**
   * Загрузка информации о текущем API ключе.
   */
  const fetchApiKeyInfo = useCallback(async () => {
    if (!user || user.plan !== "enterprise") return;

    setApiKeyLoading(true);
    setApiKeyError(null);

    try {
      const response = await fetch("/api/keys");
      if (!response.ok) {
        if (response.status === 404) {
          // Ключ не создан — это нормально
          setApiKeyInfo({ prefix: null, created_at: null, last_used_at: null });
          return;
        }
        throw new Error("Ошибка загрузки информации о ключе");
      }
      const data: ApiKeyInfo = await response.json();
      setApiKeyInfo(data);
    } catch (err) {
      setApiKeyError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setApiKeyLoading(false);
    }
  }, [user]);

  /**
   * Создание нового API ключа.
   */
  const createApiKey = async () => {
    setApiKeyLoading(true);
    setApiKeyError(null);
    setNewApiKey(null);

    try {
      const response = await fetch("/api/keys", { method: "POST" });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Ошибка создания ключа");
      }
      const data: ApiKeyCreatedResponse = await response.json();
      setNewApiKey(data.api_key);
      // Обновляем информацию о ключе
      await fetchApiKeyInfo();
    } catch (err) {
      setApiKeyError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setApiKeyLoading(false);
    }
  };

  /**
   * Отзыв API ключа.
   */
  const revokeApiKey = async () => {
    if (!confirm("Вы уверены? Текущий ключ перестанет работать.")) return;

    setApiKeyLoading(true);
    setApiKeyError(null);
    setNewApiKey(null);

    try {
      const response = await fetch("/api/keys", { method: "DELETE" });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Ошибка отзыва ключа");
      }
      setApiKeyInfo({ prefix: null, created_at: null, last_used_at: null });
    } catch (err) {
      setApiKeyError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setApiKeyLoading(false);
    }
  };

  /**
   * Копирование ключа в буфер обмена.
   */
  const copyApiKey = async () => {
    if (!newApiKey) return;
    await navigator.clipboard.writeText(newApiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Загружаем информацию о ключе для Enterprise
  useEffect(() => {
    fetchApiKeyInfo();
  }, [fetchApiKeyInfo]);

  /**
   * Загрузка настроек этикеток.
   */
  const fetchLabelPreferences = useCallback(async () => {
    if (!user) return;

    setLabelPrefsLoading(true);
    setLabelPrefsError(null);

    try {
      const prefs = await getUserPreferences();

      // Заполняем локальные состояния
      setOrgName(prefs.organization_name || "");
      setInn(prefs.inn || "");
      setLayout(prefs.preferred_layout);
      setLabelSize(prefs.preferred_label_size);
      setLabelFormat(prefs.preferred_format);
      setShowArticle(prefs.show_article);
      setShowSizeColor(prefs.show_size_color);
      setShowName(prefs.show_name);
      // Загружаем кастомные строки или пустой массив
      const lines = prefs.custom_lines || [];
      setCustomLines([lines[0] || "", lines[1] || "", lines[2] || ""]);
    } catch (err) {
      setLabelPrefsError(
        err instanceof Error ? err.message : "Ошибка загрузки настроек"
      );
    } finally {
      setLabelPrefsLoading(false);
    }
  }, [user]);

  /**
   * Сохранение настроек этикеток.
   */
  const saveLabelPreferences = async () => {
    setLabelPrefsSaving(true);
    setLabelPrefsError(null);
    setLabelPrefsSaved(false);

    try {
      // Фильтруем пустые строки для кастомных линий
      const nonEmptyCustomLines = customLines.filter((line) => line.trim() !== "");

      await updateUserPreferences({
        organization_name: orgName || null,
        inn: inn || null,
        preferred_layout: layout,
        preferred_label_size: labelSize,
        preferred_format: labelFormat,
        show_article: showArticle,
        show_size_color: showSizeColor,
        show_name: showName,
        custom_lines: nonEmptyCustomLines.length > 0 ? nonEmptyCustomLines : null,
      });
      setLabelPrefsSaved(true);
      setTimeout(() => setLabelPrefsSaved(false), 3000);
    } catch (err) {
      setLabelPrefsError(
        err instanceof Error ? err.message : "Ошибка сохранения настроек"
      );
    } finally {
      setLabelPrefsSaving(false);
    }
  };

  // Загружаем настройки этикеток
  useEffect(() => {
    fetchLabelPreferences();
  }, [fetchLabelPreferences]);

  // Extended шаблон не поддерживает размер 58x30 — автопереключение
  useEffect(() => {
    if (layout === "extended" && labelSize === "58x30") {
      setLabelSize("58x40");
    }
  }, [layout, labelSize]);

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

      {/* Настройки этикеток */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Tag className="w-5 h-5 text-emerald-600" />
            Настройки этикеток
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Ошибка */}
          {labelPrefsError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{labelPrefsError}</p>
            </div>
          )}

          {/* Успех */}
          {labelPrefsSaved && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-3">
              <Check className="w-5 h-5 text-emerald-600" />
              <p className="text-sm text-emerald-800">Настройки сохранены</p>
            </div>
          )}

          {/* Загрузка */}
          {labelPrefsLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
            </div>
          )}

          {/* Форма настроек */}
          {!labelPrefsLoading && (
            <div className="space-y-6">
              {/* Название организации и ИНН */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-2">
                    Название организации
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <input
                    type="text"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="ИП Иванов И.И."
                    className="w-full px-4 py-3 rounded-lg border border-warm-gray-300 bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                  <p className="text-xs text-warm-gray-500 mt-1">
                    Обязательное поле. Отображается на всех этикетках.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-2">
                    ИНН
                  </label>
                  <input
                    type="text"
                    value={inn}
                    onChange={(e) => setInn(e.target.value)}
                    placeholder="1234567890"
                    maxLength={12}
                    className="w-full px-4 py-3 rounded-lg border border-warm-gray-300 bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                  <p className="text-xs text-warm-gray-500 mt-1">
                    Отображается на этикетке шаблона Расширенный (10 или 12 цифр)
                  </p>
                </div>
              </div>

              {/* Кастомные строки для Extended шаблона */}
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <label className="block text-sm font-medium text-amber-800 mb-3">
                  Кастомные строки для Расширенного шаблона
                </label>
                <p className="text-xs text-amber-700 mb-3">
                  До 3 дополнительных строк текста на этикетке (только для Расширенного шаблона)
                </p>
                <div className="space-y-2">
                  {[0, 1, 2].map((index) => (
                    <input
                      key={index}
                      type="text"
                      value={customLines[index]}
                      onChange={(e) => {
                        const newLines = [...customLines];
                        newLines[index] = e.target.value;
                        setCustomLines(newLines);
                      }}
                      placeholder={
                        index === 0
                          ? "Строка 1 (например: Сделано с любовью)"
                          : index === 1
                            ? "Строка 2 (например: www.myshop.ru)"
                            : "Строка 3"
                      }
                      maxLength={50}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-amber-300 bg-white
                        focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                    />
                  ))}
                </div>
              </div>

              {/* Кнопка сохранения */}
              <div className="flex justify-end pt-4 border-t border-warm-gray-200">
                <Button
                  onClick={saveLabelPreferences}
                  disabled={labelPrefsSaving}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {labelPrefsSaving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  Сохранить настройки
                </Button>
              </div>
            </div>
          )}

          {/* Информация */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Эти настройки автоматически применяются при генерации этикеток из
              Excel на странице генерации.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* API ключи (только для Enterprise) */}
      {user.plan === "enterprise" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5 text-emerald-600" />
              API ключ
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Ошибка */}
            {apiKeyError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{apiKeyError}</p>
              </div>
            )}

            {/* Новый ключ — показываем только один раз */}
            {newApiKey && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-amber-800">
                      Сохраните ключ! Он больше не будет показан.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 px-3 py-2 bg-white border border-amber-300 rounded font-mono text-sm break-all">
                    {newApiKey}
                  </code>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={copyApiKey}
                    className="flex-shrink-0"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Загрузка */}
            {apiKeyLoading && !apiKeyInfo && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
              </div>
            )}

            {/* Информация о ключе или кнопка создания */}
            {apiKeyInfo && !apiKeyLoading && (
              <>
                {apiKeyInfo.prefix ? (
                  // Ключ существует
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                          Префикс ключа
                        </label>
                        <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                          <code className="text-warm-gray-900 font-mono">
                            {apiKeyInfo.prefix}...
                          </code>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                          Создан
                        </label>
                        <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                          <p className="text-warm-gray-900">
                            {apiKeyInfo.created_at
                              ? formatDate(apiKeyInfo.created_at)
                              : "—"}
                          </p>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                          Последнее использование
                        </label>
                        <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                          <p className="text-warm-gray-900">
                            {apiKeyInfo.last_used_at
                              ? formatDate(apiKeyInfo.last_used_at)
                              : "Никогда"}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Button
                        variant="secondary"
                        onClick={revokeApiKey}
                        disabled={apiKeyLoading}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Отозвать ключ
                      </Button>
                      <p className="text-sm text-warm-gray-500">
                        После отзыва можно создать новый ключ
                      </p>
                    </div>
                  </div>
                ) : (
                  // Ключа нет
                  <div className="text-center py-6">
                    <Key className="w-12 h-12 text-warm-gray-300 mx-auto mb-4" />
                    <p className="text-warm-gray-600 mb-4">
                      API ключ позволяет интегрировать KleyKod в ваши системы
                    </p>
                    <Button
                      onClick={createApiKey}
                      disabled={apiKeyLoading}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      {apiKeyLoading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Key className="w-4 h-4 mr-2" />
                      )}
                      Создать API ключ
                    </Button>
                  </div>
                )}
              </>
            )}

            {/* Документация */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Документация API:</strong>{" "}
                <a
                  href="/docs"
                  target="_blank"
                  className="underline hover:no-underline"
                >
                  https://kleykod.ru/docs
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      )}

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
