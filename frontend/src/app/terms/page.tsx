import Link from "next/link";

export const metadata = {
  title: "Условия использования | KleyKod",
  description: "Пользовательское соглашение сервиса KleyKod",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-sm p-8 md:p-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            Пользовательское соглашение
          </h1>

          <div className="prose prose-gray max-w-none">
            <p className="text-sm text-gray-500 mb-8">
              Дата вступления в силу: «___» ____________ 2025 г.
              <br />
              Последнее обновление: «___» ____________ 2025 г.
            </p>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                1. Общие положения
              </h2>
              <p className="text-gray-700 mb-4">
                1.1. Настоящее Пользовательское соглашение (далее — «Соглашение»)
                регулирует отношения между:
              </p>
              <div className="bg-gray-100 p-4 rounded-lg mb-4">
                <p className="text-gray-700">
                  <strong>Наименование:</strong> [________________]
                  <br />
                  <strong>ИНН:</strong> [________________]
                  <br />
                  <strong>ОГРН/ОГРНИП:</strong> [________________]
                  <br />
                  <strong>Адрес:</strong> [________________]
                </p>
              </div>
              <p className="text-gray-700 mb-4">
                (далее — «Исполнитель») и любым лицом, использующим сервис
                KleyKod (далее — «Пользователь»).
              </p>
              <p className="text-gray-700 mb-4">
                1.2. Сервис KleyKod (далее — «Сервис») — программное обеспечение,
                доступное по адресу https://kleykod.ru и через Telegram-бота
                @kleykod_bot, предназначенное для объединения этикеток
                Wildberries и кодов маркировки системы «Честный знак» на одном
                носителе.
              </p>
              <p className="text-gray-700 mb-4">
                1.3. Использование Сервиса означает полное и безоговорочное
                принятие Пользователем условий настоящего Соглашения в
                соответствии со статьей 438 Гражданского кодекса Российской
                Федерации (акцепт оферты).
              </p>
              <p className="text-gray-700 mb-4">
                1.4. В случае несогласия с условиями Соглашения Пользователь
                обязан немедленно прекратить использование Сервиса.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                2. Предмет Соглашения
              </h2>
              <p className="text-gray-700 mb-4">
                2.1. Исполнитель предоставляет Пользователю право использования
                Сервиса на условиях простой (неисключительной) лицензии для
                следующих целей:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>
                  Загрузка PDF-файлов с этикетками маркетплейса Wildberries
                </li>
                <li>
                  Загрузка файлов с кодами маркировки системы «Честный знак»
                </li>
                <li>
                  Генерация объединенных этикеток в формате PDF
                </li>
                <li>
                  Проверка корректности кодов маркировки (Pre-flight check)
                </li>
              </ul>
              <p className="text-gray-700 mb-4">
                2.2. Сервис предоставляется на условиях «как есть» (as is).
                Исполнитель не гарантирует, что Сервис будет соответствовать
                целям и ожиданиям Пользователя.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                3. Тарифы и оплата
              </h2>
              <p className="text-gray-700 mb-4">
                3.1. Сервис предоставляется на следующих условиях:
              </p>
              <div className="overflow-x-auto mb-4">
                <table className="min-w-full border border-gray-300">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border border-gray-300 px-4 py-2 text-left">
                        Тариф
                      </th>
                      <th className="border border-gray-300 px-4 py-2 text-left">
                        Лимит генераций
                      </th>
                      <th className="border border-gray-300 px-4 py-2 text-left">
                        Стоимость
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Free</td>
                      <td className="border border-gray-300 px-4 py-2">
                        50 этикеток/день
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        Бесплатно
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Pro</td>
                      <td className="border border-gray-300 px-4 py-2">
                        1000 этикеток/день
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        299 руб/мес
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">
                        Enterprise
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        Без ограничений
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        1499 руб/мес
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-gray-700 mb-4">
                3.2. Оплата производится через платёжную систему ЮКасса
                (ООО «ЮКАССА», ИНН 7733812159) или иные способы, указанные в Сервисе.
              </p>
              <p className="text-gray-700 mb-4">
                3.3. Подписка продлевается автоматически, если Пользователь не
                отменил её до окончания текущего периода.
              </p>
              <p className="text-gray-700 mb-4">
                3.4. Возврат денежных средств осуществляется в соответствии с
                законодательством Российской Федерации и правилами платежных
                систем.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                4. Права и обязанности сторон
              </h2>
              <h3 className="text-lg font-medium text-gray-800 mb-3">
                4.1. Пользователь обязуется:
              </h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>
                  Использовать Сервис исключительно в законных целях
                </li>
                <li>
                  Загружать только собственные файлы или файлы, на использование
                  которых имеется право
                </li>
                <li>
                  Не предпринимать действий, направленных на нарушение
                  работоспособности Сервиса
                </li>
                <li>
                  Не передавать третьим лицам данные для доступа к своей учетной
                  записи
                </li>
                <li>
                  Соблюдать требования законодательства о маркировке товаров
                </li>
              </ul>
              <h3 className="text-lg font-medium text-gray-800 mb-3">
                4.2. Пользователь имеет право:
              </h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>
                  Использовать функционал Сервиса в соответствии с выбранным
                  тарифом
                </li>
                <li>
                  Обращаться в службу поддержки по вопросам работы Сервиса
                </li>
                <li>
                  Отказаться от использования Сервиса в любое время
                </li>
              </ul>
              <h3 className="text-lg font-medium text-gray-800 mb-3">
                4.3. Исполнитель обязуется:
              </h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>
                  Обеспечивать работоспособность Сервиса в режиме 24/7, за
                  исключением периодов технического обслуживания
                </li>
                <li>
                  Обеспечивать конфиденциальность данных Пользователя
                </li>
                <li>
                  Своевременно информировать о существенных изменениях в работе
                  Сервиса
                </li>
              </ul>
              <h3 className="text-lg font-medium text-gray-800 mb-3">
                4.4. Исполнитель имеет право:
              </h3>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>
                  Изменять функционал Сервиса без предварительного уведомления
                </li>
                <li>
                  Приостанавливать работу Сервиса для технического обслуживания
                </li>
                <li>
                  Блокировать доступ Пользователя при нарушении условий
                  Соглашения
                </li>
                <li>
                  Изменять тарифы с уведомлением за 14 дней до вступления
                  изменений в силу
                </li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                5. Ограничение ответственности
              </h2>
              <p className="text-gray-700 mb-4">
                5.1. Исполнитель не несет ответственности за:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>
                  Качество и содержание файлов, загружаемых Пользователем
                </li>
                <li>
                  Соответствие сгенерированных этикеток требованиям конкретных
                  торговых площадок
                </li>
                <li>
                  Корректность кодов маркировки, предоставленных Пользователем
                </li>
                <li>
                  Убытки, возникшие в результате использования или невозможности
                  использования Сервиса
                </li>
                <li>
                  Действия третьих лиц, в том числе платежных систем
                </li>
                <li>
                  Перебои в работе Сервиса, вызванные обстоятельствами
                  непреодолимой силы
                </li>
              </ul>
              <p className="text-gray-700 mb-4">
                5.2. Совокупная ответственность Исполнителя перед Пользователем
                ограничивается суммой, уплаченной Пользователем за использование
                Сервиса в течение последних 3 (трех) месяцев.
              </p>
              <p className="text-gray-700 mb-4">
                5.3. Пользователь самостоятельно несет ответственность за
                соблюдение требований законодательства о маркировке товаров и
                правил работы с системой «Честный знак».
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                6. Интеллектуальная собственность
              </h2>
              <p className="text-gray-700 mb-4">
                6.1. Исключительные права на Сервис, включая программный код,
                дизайн, логотипы и товарные знаки, принадлежат Исполнителю.
              </p>
              <p className="text-gray-700 mb-4">
                6.2. Пользователю предоставляется ограниченное право
                использования Сервиса в соответствии с его функциональным
                назначением.
              </p>
              <p className="text-gray-700 mb-4">
                6.3. Запрещается копирование, модификация, распространение,
                декомпиляция или иное использование Сервиса, выходящее за рамки
                настоящего Соглашения.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                7. Конфиденциальность
              </h2>
              <p className="text-gray-700 mb-4">
                7.1. Обработка персональных данных Пользователя осуществляется в
                соответствии с{" "}
                <Link href="/privacy" className="text-blue-600 hover:underline">
                  Политикой конфиденциальности
                </Link>
                .
              </p>
              <p className="text-gray-700 mb-4">
                7.2. Исполнитель обязуется не разглашать информацию о содержании
                файлов, загружаемых Пользователем.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                8. Порядок разрешения споров
              </h2>
              <p className="text-gray-700 mb-4">
                8.1. Все споры и разногласия разрешаются путем переговоров.
              </p>
              <p className="text-gray-700 mb-4">
                8.2. Претензионный порядок обязателен. Срок рассмотрения
                претензии — 30 (тридцать) календарных дней с момента получения.
              </p>
              <p className="text-gray-700 mb-4">
                8.3. При невозможности урегулирования спора в претензионном
                порядке спор передается на рассмотрение в суд по месту нахождения
                Исполнителя.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                9. Заключительные положения
              </h2>
              <p className="text-gray-700 mb-4">
                9.1. Настоящее Соглашение вступает в силу с момента начала
                использования Сервиса Пользователем и действует бессрочно.
              </p>
              <p className="text-gray-700 mb-4">
                9.2. Исполнитель вправе в одностороннем порядке изменять условия
                Соглашения. Изменения вступают в силу с момента публикации новой
                редакции на сайте Сервиса.
              </p>
              <p className="text-gray-700 mb-4">
                9.3. Продолжение использования Сервиса после внесения изменений
                означает согласие Пользователя с новой редакцией Соглашения.
              </p>
              <p className="text-gray-700 mb-4">
                9.4. Если какое-либо положение Соглашения будет признано
                недействительным, это не влияет на действительность остальных
                положений.
              </p>
              <p className="text-gray-700 mb-4">
                9.5. К отношениям сторон применяется законодательство Российской
                Федерации.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                10. Контактная информация
              </h2>
              <div className="bg-gray-100 p-4 rounded-lg">
                <p className="text-gray-700">
                  <strong>Наименование:</strong> [________________]
                  <br />
                  <strong>ИНН:</strong> [________________]
                  <br />
                  <strong>Адрес:</strong> [________________]
                  <br />
                  <strong>Email:</strong> support@kleykod.ru
                  <br />
                  <strong>Telegram:</strong> @kleykod_support
                </p>
              </div>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-200 flex gap-4">
            <Link
              href="/"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              &larr; Вернуться на главную
            </Link>
            <span className="text-gray-300">|</span>
            <Link
              href="/privacy"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Политика конфиденциальности
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
