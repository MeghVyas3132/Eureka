import { fireEvent, render, screen } from "@testing-library/react";
import { FormEvent } from "react";

import AuthCard from "@/components/auth/AuthCard";

describe("AuthCard", () => {
  it("renders title and triggers submit", () => {
    const onSubmit = jest.fn((event: FormEvent<HTMLFormElement>) => event.preventDefault());

    render(
      <AuthCard
        title="Login"
        subtitle="Use your account"
        ctaLabel="Sign In"
        footer={<span>Footer</span>}
        onSubmit={onSubmit}
        loading={false}
        error=""
      >
        <input aria-label="email" />
      </AuthCard>,
    );

    expect(screen.getByText("Login")).toBeInTheDocument();
    fireEvent.submit(screen.getByRole("button", { name: "Sign In" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
