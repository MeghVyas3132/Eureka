import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import AdminUsersPage from "@/app/admin/users/page";
import { api } from "@/lib/api";

const pushMock = jest.fn();
const replaceMock = jest.fn();
const routerMock = {
  push: pushMock,
  replace: replaceMock,
};

jest.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

jest.mock("@/store/authStore", () => ({
  useAuthStore: () => ({
    initializeAuth: jest.fn(),
    user: {
      id: "admin-id",
      username: "admin",
      email: "admin@aexiz.com",
      role: "admin",
      subscription_tier: "admin",
      created_at: "2026-04-25T00:00:00Z",
    },
    logout: jest.fn(),
  }),
}));

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    patch: jest.fn(),
  },
}));

describe("Admin users page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockImplementation((url: string) => {
      if (url === "/api/v1/admin/users") {
        return Promise.resolve({
          data: {
            data: [
              {
                id: "user-id",
                username: "store_user",
                email: "user@example.com",
                role: "merchandiser",
                subscription_tier: "individual-plus",
                created_at: "2026-04-25T00:00:00Z",
                layout_count: 3,
              },
            ],
            message: "ok",
          },
        });
      }

      return Promise.resolve({
        data: {
          data: [
            { tier: "individual-plus", annual_planogram_limit: 15, is_unlimited: false },
            { tier: "individual-pro", annual_planogram_limit: 45, is_unlimited: false },
          ],
          message: "ok",
        },
      });
    });

    (api.patch as jest.Mock).mockResolvedValue({
      data: {
        data: { tier: "individual-plus", annual_planogram_limit: 20, is_unlimited: false },
        message: "saved",
      },
    });
  });

  it("renders user database rows and updates plan limits", async () => {
    render(<AdminUsersPage />);

    expect(await screen.findByText("User Database")).toBeInTheDocument();
    expect(await screen.findByText("store_user")).toBeInTheDocument();
    expect(screen.queryByText("Password")).not.toBeInTheDocument();

    const input = await screen.findByLabelText("individual-plus-annual-limit");
    fireEvent.change(input, { target: { value: "20" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Save" })[0]);

    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith("/api/v1/admin/plan-limits/individual-plus", {
        annual_planogram_limit: 20,
        is_unlimited: false,
      }),
    );
  });
});
