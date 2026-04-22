import java.sql.*;

public class LoginExample {
    public static void main(String[] args) throws Exception {

        Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/testdb", "root", "password");

        Statement stmt = conn.createStatement();

        String sql = "SELECT * FROM users WHERE username = '" + username +
                     "' AND password = '" + password + "'";

        ResultSet rs = stmt.executeQuery(sql);

        if (rs.next()) {
            System.out.println("登录成功！");
        } else {
            System.out.println("登录失败！");
        }

        conn.close();
    }
}
