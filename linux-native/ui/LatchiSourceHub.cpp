#include "LatchiSourceHub.h"
#include <QAbstractButton>
#include <QEnterEvent>
#include <QEvent>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPainter>
#include <QPainterPath>
#include <QPushButton>
#include <QScrollArea>
#include <QVariantAnimation>
#include <QVBoxLayout>

namespace CloudStream {
namespace {
class SourceCard final : public QAbstractButton {
public:
    explicit SourceCard(const LatchiSourceDefinition &source, QWidget *parent)
        : QAbstractButton(parent), image_(":/sourcecards/" + source.card), accent_(source.accent) {
        setObjectName("latchiSource_" + source.id);
        setProperty("providerId", source.id);
        setAccessibleName(source.arabic + " — " + source.english);
        setToolTip(source.arabic + "\n" + source.english + "\nفتح المصدر أو تثبيت إضافته بعد موافقتك");
        setFocusPolicy(Qt::StrongFocus);
        setCursor(Qt::PointingHandCursor);
        setMinimumWidth(220);
        setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
        animation_ = new QVariantAnimation(this);
        animation_->setDuration(140);
        QObject::connect(animation_, &QVariantAnimation::valueChanged, this, [this](const QVariant &value) {
            hover_ = value.toReal(); update();
        });
    }
    QSize sizeHint() const override { return QSize(450, 150); }
protected:
    void enterEvent(QEnterEvent *event) override { animate(1); QAbstractButton::enterEvent(event); }
    void leaveEvent(QEvent *event) override { animate(0); QAbstractButton::leaveEvent(event); }
    void focusInEvent(QFocusEvent *event) override { update(); QAbstractButton::focusInEvent(event); }
    void focusOutEvent(QFocusEvent *event) override { update(); QAbstractButton::focusOutEvent(event); }
    void paintEvent(QPaintEvent *) override {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);
        painter.setRenderHint(QPainter::SmoothPixmapTransform);
        const QRectF target = QRectF(rect()).adjusted(3, 3, -3, -3);
        painter.setOpacity(isEnabled() ? 1 : .55);
        QRectF picture = target; picture.setHeight(target.width() / 3.0); picture.moveCenter(target.center());
        painter.drawPixmap(picture.toRect(), image_);
        if (hover_ > 0 || hasFocus() || isDown()) {
            QColor color = accent_;
            color.setAlphaF(hasFocus() ? 1 : qMax(.12, hover_ * .7));
            painter.setPen(QPen(color, hasFocus() ? 3 : 2));
            painter.setBrush(Qt::NoBrush);
            painter.drawRoundedRect(target, target.height() * .08, target.height() * .08);
        }
    }
private:
    void animate(qreal target) {
        animation_->stop(); animation_->setStartValue(hover_); animation_->setEndValue(target); animation_->start();
    }
    QPixmap image_;
    QColor accent_;
    QVariantAnimation *animation_{};
    qreal hover_ = 0;
};
}

QList<LatchiSourceDefinition> LatchiSourceHub::sources() {
    return {
        {"3isk", QString::fromUtf8("قصة عشق ١"), "3isk", "qissat-eshq-1.png", "#ed6379"},
        {"eseek", QString::fromUtf8("قصة عشق ٢"), "Eshek", "qissat-eshq-2.png", "#f1af6c"},
        {"Krmzy", QString::fromUtf8("قرمزي"), "Krmzy", "krmzy.png", "#bc83f8"},
        {"MyCimaProvider", QString::fromUtf8("ماي سيما"), "MyCima", "mycima.png", "#69cdc3"},
        {"Topcinema", QString::fromUtf8("توب سينما"), "TopCinema", "topcinema.png", "#74b6ff"},
        {"TukTukcima", QString::fromUtf8("توك توك سيما"), "TukTukcima", "tuktukcima.png", "#f1d075"},
        {"Tuniflix", QString::fromUtf8("تونيفليكس"), "Tuniflix", "tuniflix.png", "#b398fa"},
        {"Wecima", QString::fromUtf8("وي سيما"), "WeCima", "wecima.png", "#f490bb"}
    };
}

LatchiSourceHub::LatchiSourceHub(QWidget *parent) : QWidget(parent) {
    setObjectName("latchiSourceHub");
    setLayoutDirection(Qt::RightToLeft);
    auto *outer = new QVBoxLayout(this);
    outer->setContentsMargins(0, 0, 0, 0);
    scroll_ = new QScrollArea(this);
    scroll_->setWidgetResizable(true);
    scroll_->setFrameShape(QFrame::NoFrame);
    scroll_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scroll_->viewport()->installEventFilter(this);
    auto *content = new QWidget;
    content->setObjectName("latchiSourceContent");
    auto *layout = new QVBoxLayout(content);
    layout->setContentsMargins(28, 24, 28, 24);
    layout->setSpacing(14);
    auto *top = new QHBoxLayout;
    top->setSpacing(14);
    auto *logo = new QLabel;
    logo->setPixmap(QPixmap(":/assets/latchi-launcher.png").scaled(54, 54, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    logo->setFixedSize(54, 54);
    auto *brand = new QLabel("LATCHI WATCHING");
    brand->setStyleSheet("font-size:20px; font-weight:750; color:#f3f5fd; letter-spacing:1px;");
    brand->setLayoutDirection(Qt::LeftToRight);
    top->addWidget(logo);
    top->addWidget(brand);
    top->addStretch();
    auto *extensions = new QPushButton(QString::fromUtf8("إدارة الإضافات"));
    extensions->setObjectName("latchiManageExtensions");
    extensions->setMinimumHeight(38);
    connect(extensions, &QPushButton::clicked, this, &LatchiSourceHub::extensionsRequested);
    top->addWidget(extensions);
    layout->addLayout(top);
    auto *heading = new QLabel(QString::fromUtf8("اختر مصدرك. وابدأ المشاهدة."));
    heading->setWordWrap(true);
    heading->setStyleSheet("font-size:26px; font-weight:750; color:#fafbff;");
    layout->addWidget(heading);
    auto *subtitle = new QLabel(QString::fromUtf8("ثمانية مصادر عربية · إضافات CloudStream حقيقية · مشغّل أصلي داخل التطبيق"));
    subtitle->setWordWrap(true);
    subtitle->setStyleSheet("font-size:13px; color:#98a4bb;");
    layout->addWidget(subtitle);
    grid_ = new QGridLayout;
    grid_->setHorizontalSpacing(12);
    grid_->setVerticalSpacing(10);
    for (const auto &source : sources()) {
        auto *card = new SourceCard(source, content);
        connect(card, &QAbstractButton::clicked, this, [this, id = source.id] { emit sourceActivated(id); });
        cards_ << card;
    }
    layout->addLayout(grid_);
    message_ = new QLabel(QString::fromUtf8("تُثبَّت الإضافة عند اختيار المصدر وبعد موافقتك. لا تُحمَّل أي إضافة تلقائيًا."));
    message_->setObjectName("latchiSourceMessage");
    message_->setTextFormat(Qt::PlainText);
    message_->setWordWrap(true);
    message_->setMinimumHeight(35);
    message_->setStyleSheet("color:#a0aac0; font-size:12px;");
    layout->addWidget(message_);
    auto *bottom = new QHBoxLayout;
    auto *privacy = new QLabel(QString::fromUtf8("ملفك محفوظ محليًا • نسخة مستقلة عن إصدار Electron السابق"));
    privacy->setWordWrap(true);
    privacy->setStyleSheet("color:#67748d; font-size:11px;");
    bottom->addWidget(privacy, 1);
    auto *network = new QPushButton(QString::fromUtf8("فتح بث مباشر"));
    network->setMinimumHeight(36);
    network->setAccessibleName(QString::fromUtf8("فتح رابط بث لديك حق مشاهدته"));
    connect(network, &QPushButton::clicked, this, &LatchiSourceHub::networkRequested);
    bottom->addWidget(network);
    layout->addLayout(bottom);
    layout->addStretch();
    scroll_->setWidget(content);
    outer->addWidget(scroll_);
    relayout(1000);
}

void LatchiSourceHub::setMessage(const QString &message, bool error) {
    message_->setText(message);
    message_->setStyleSheet(error ? "color:#ff9aab; font-size:12px;" : "color:#a0aac0; font-size:12px;");
}
void LatchiSourceHub::setBusy(bool busy, const QString &message) {
    busy_ = busy;
    for (auto *card : cards_) card->setEnabled(!busy);
    if (!message.isEmpty()) setMessage(message);
}
bool LatchiSourceHub::eventFilter(QObject *object, QEvent *event) {
    if (object == scroll_->viewport() && event->type() == QEvent::Resize)
        relayout(scroll_->viewport()->width());
    return QWidget::eventFilter(object, event);
}
void LatchiSourceHub::relayout(int width) {
    const int columns = width >= 1000 ? 3 : width >= 610 ? 2 : 1;
    while (auto *item = grid_->takeAt(0)) delete item;
    for (int col = 0; col < 3; ++col) grid_->setColumnStretch(col, col < columns ? 1 : 0);
    const int cardWidth = qMax(220, (width - 56 - 12 * (columns - 1)) / columns);
    for (int i = 0; i < cards_.size(); ++i) {
        cards_[i]->setFixedHeight(cardWidth / 3 + 6);
        grid_->addWidget(cards_[i], i / columns, i % columns);
    }
    columns_ = columns;
}
}
