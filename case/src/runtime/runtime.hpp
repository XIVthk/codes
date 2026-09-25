// runtime.hpp - Case语言运行时库
#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <variant>
#include <memory>
#include <stdexcept>

namespace case_runtime {

// ==================== 类型枚举 ====================
enum class TypeKind {
    Int, Float, Bool, Str, Bytes,
    Hex, Bin,
    Any, Auto,
    Fatal,
    Void,
    Uninit  // 未初始化占位符，如 int()
};

// ==================== Fatal 错误类型 ====================
struct Fatal {
    std::string repr;      // 错误信息
    std::string arg;       // 自动填充的上下文，如 <fn!divide, int!str>
    std::string type;      // 错误类型，如 Type, DivByZero
    
    Fatal(std::string repr = "", std::string arg = "", std::string type = "")
        : repr(repr), arg(arg), type(type) {}
    
    // 未接收的Fatal会panic（在析构时检查）
    ~Fatal() {
        // 如果未被消费，触发panic
        // 实际实现需要更复杂的机制
    }
    
    std::string to_string() const {
        if (repr.empty() && arg.empty() && type.empty())
            return "Fatal";
        return "Fatal: " + type + "[" + repr + "]<" + arg + ">";
    }
};

// ==================== Hex 类型 (32位无符号) ====================
class Hex {
private:
    uint32_t value_;
    static constexpr uint32_t BIT_MASK = 0xFFFFFFFF;
    
public:
    // 构造函数
    Hex() : value_(0) {}
    explicit Hex(uint32_t v) : value_(v & BIT_MASK) {}
    explicit Hex(int v) : value_(static_cast<uint32_t>(v) & BIT_MASK) {}
    explicit Hex(bool v) : value_(v ? 1 : 0) {}
    explicit Hex(float v) : value_(static_cast<uint32_t>(static_cast<int>(v)) & BIT_MASK) {}
    
    // 从bin转换（可能截断）
    explicit Hex(const class Bin& b);
    
    // 类型转换
    uint32_t to_uint() const { return value_; }
    int to_int() const { return static_cast<int>(value_); }  // 默认无符号
    int to_signed() const { return static_cast<int>(value_); } // 有符号解释
    bool to_bool() const { return value_ != 0; }
    float to_float() const { return static_cast<float>(value_); }
    
    // 获取值
    uint32_t value() const { return value_; }
    
    // 输出格式
    std::string to_string() const {
        char buf[16];
        snprintf(buf, sizeof(buf), "hex<0x%08X>", value_);
        return std::string(buf);
    }
    
    // ===== 位运算操作符 (带#前缀) =====
    Hex operator&(const Hex& other) const { return Hex(value_ & other.value_); }
    Hex operator|(const Hex& other) const { return Hex(value_ | other.value_); }
    Hex operator^(const Hex& other) const { return Hex(value_ ^ other.value_); }
    Hex operator~() const { return Hex(~value_); }
    Hex operator+(const Hex& other) const { return Hex(value_ + other.value_); }
    Hex operator-(const Hex& other) const { return Hex(value_ - other.value_); }
    Hex operator*(const Hex& other) const { return Hex(value_ * other.value_); }
    Hex operator/(const Hex& other) const { 
        if (other.value_ == 0) throw Fatal("Division by zero", "<hex/0>", "DivByZero");
        return Hex(value_ / other.value_); 
    }
    
    // 移位操作
    Hex operator<<(int shift) const { return Hex(value_ << (shift & 31)); }
    Hex operator>>(int shift) const { return Hex(value_ >> (shift & 31)); }
    Hex operator<<(bool shift) const { return Hex(value_ << (shift ? 1 : 0)); }
    Hex operator>>(bool shift) const { return Hex(value_ >> (shift ? 1 : 0)); }
    Hex operator<<(float shift) const { return Hex(value_ << (static_cast<int>(shift) & 31)); }
    Hex operator>>(float shift) const { return Hex(value_ >> (static_cast<int>(shift) & 31)); }
    
    // 与int/bool/float的混合运算（自动转换）
    friend Hex operator+(const Hex& h, int v) { return Hex(h.value_ + static_cast<uint32_t>(v)); }
    friend Hex operator+(int v, const Hex& h) { return Hex(static_cast<uint32_t>(v) + h.value_); }
    // ... 其他类似
};

// ==================== Bin 类型 (可变长位序列) ====================
class Bin {
private:
    std::vector<uint8_t> bytes_;  // 存储位，每个字节8位
    size_t bit_length_;            // 实际有效位数
    
    // 内部辅助函数
    void trim_leading_zeros();     // 移除前导零（但保留至少1位）
    void pad_to_power_of_two();    // 补齐到2^n位 (n>0)
    void ensure_capacity(size_t bits);
    
public:
    // 构造函数
    Bin() : bit_length_(0) {}
    explicit Bin(const std::vector<uint8_t>& bytes, size_t bit_len);
    explicit Bin(uint32_t hex_val);  // 从hex转换
    explicit Bin(const Hex& h);      // 从hex转换
    
    // 从二进制字符串构造 (如 "1010")
    static Bin from_binary_string(const std::string& binary_str);
    
    // 从十六进制字符串构造
    static Bin from_hex_string(const std::string& hex_str);
    
    // 类型转换
    Hex to_hex() const;               // 可能截断
    uint32_t to_uint() const;         // 默认无符号
    int to_signed() const;            // 有符号解释
    bool to_bool() const { return bit_length_ > 0 && bytes_[0] != 0; }
    
    // 访问
    size_t bit_length() const { return bit_length_; }
    uint8_t get_bit(size_t pos) const;
    void set_bit(size_t pos, uint8_t bit);
    
    // 输出格式
    std::string to_string() const {
        std::string result = "bin<0b";
        for (size_t i = 0; i < bit_length_; ++i) {
            result += get_bit(bit_length_ - 1 - i) ? '1' : '0';
        }
        result += ">";
        return result;
    }
    
    // ===== 位运算操作符 =====
    Bin operator&(const Bin& other) const;
    Bin operator|(const Bin& other) const;
    Bin operator^(const Bin& other) const;
    Bin operator~() const;
    
    // 移位操作
    Bin operator<<(int shift) const;
    Bin operator>>(int shift) const;
    Bin operator<<(bool shift) const { return *this << (shift ? 1 : 0); }
    Bin operator>>(bool shift) const { return *this >> (shift ? 1 : 0); }
    Bin operator<<(float shift) const { return *this << static_cast<int>(shift); }
    Bin operator>>(float shift) const { return *this >> static_cast<int>(shift); }
    
    // 与hex混用
    friend Bin operator&(const Bin& b, const Hex& h) { return b & Bin(h); }
    friend Bin operator&(const Hex& h, const Bin& b) { return Bin(h) & b; }
    // ... 其他类似
};

// ==================== Any 类型 (动态类型) ====================
class Any {
private:
    using Storage = std::variant<
        int, float, bool, std::string, std::vector<uint8_t>,
        Hex, Bin, Fatal, std::monostate  // monostate表示未初始化
    >;
    
    Storage data_;
    TypeKind current_type_;
    
    // 类型升级逻辑
    void upgrade_to_float();  // int → float
    void upgrade_to_bytes();  // str → bytes
    void upgrade_to_bool();   // null → bool
    
public:
    Any() : current_type_(TypeKind::Uninit) {}
    
    template<typename T>
    Any(T value) { assign(value); }
    
    template<typename T>
    void assign(T value);
    
    TypeKind type() const { return current_type_; }
    
    // 类型检查和获取
    template<typename T>
    bool is() const;
    
    template<typename T>
    T get() const;
    
    // 临时类型适配 (用于 if! 等上下文)
    bool to_bool_temp() const;  // 临时转为bool，不改变自身
    
    // 永久类型升级
    void upgrade(TypeKind target);
    
    // 输出
    std::string to_string() const;
    
    // ===== 运算符重载 =====
    Any operator+(const Any& other) const;
    Any operator-(const Any& other) const;
    Any operator*(const Any& other) const;
    Any operator/(const Any& other) const;
    // ... 其他
};

// ==================== 辅助函数 ====================

// 类型检查函数 instance()
template<typename... Args>
void instance_check(const Args&... args) {
    // 实现类型一致性检查
    // 如果不一致，抛出Fatal
}

// signed 转换
inline int signed_hex(const Hex& h) {
    return h.to_signed();
}

inline int signed_bin(const Bin& b) {
    return b.to_signed();
}

} // namespace case_runtime