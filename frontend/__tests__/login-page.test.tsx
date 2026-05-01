import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import LoginPage from "@/app/(auth)/login/page";

const pushMock = jest.fn();
const replaceMock = jest.fn();
const routerMock = {
  push: pushMock,
  replace: replaceMock,
};
const loginMock = jest.fn();
const initializeAuthMock = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => routerMock,
  useSearchParams: () =>
    ({
      get: () => null,
    }) as URLSearchParams,
}));

jest.mock("@/store/authStore", () => ({
  getPostLoginRoute: (user: { role: string }) => (user.role === "admin" ? "/super-admin" : "/dashboard"),
  useAuthStore: () => ({
    login: loginMock,
    token: null,
    user: null,
    initializeAuth: initializeAuthMock,
  }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("logs in with credentials only and routes non-admin users to dashboard", async () => {
    loginMock.mockResolvedValue({
      id: "user-id",
      first_name: "Store",
      last_name: "User",
      username: "merch_user",
      email: "user@example.com",
      company_name: "Retail Co",
      phone_number: "1234567890",
      role: "merchandiser",
      subscription_tier: "individual-plus",
      approval_status: "approved",
      created_at: "2026-04-25T00:00:00Z",
    });

    const user = userEvent.setup();
    render(<LoginPage />);

    expect(screen.queryByRole("button", { name: "Admin" })).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledWith("user@example.com", "password123"));
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
    expect(initializeAuthMock).toHaveBeenCalled();
  });

  it("routes admin users to the super admin page after login", async () => {
    loginMock.mockResolvedValue({
      id: "admin-id",
      first_name: "Super",
      last_name: "Admin",
      username: "admin",
      email: "admin@aexiz.com",
      company_name: "Eureka",
      phone_number: null,
      role: "admin",
      subscription_tier: "admin",
      approval_status: "approved",
      created_at: "2026-04-25T00:00:00Z",
    });

    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "admin@aexiz.com");
    await user.type(screen.getByLabelText("Password"), "qwerty123");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledWith("admin@aexiz.com", "qwerty123"));
    expect(pushMock).toHaveBeenCalledWith("/super-admin");
  });
});
